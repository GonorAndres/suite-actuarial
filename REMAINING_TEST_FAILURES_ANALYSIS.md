# Analysis of 2 Remaining Test Failures

## Summary

Both failing tests have **real issues** - one is a bootstrap algorithm problem, and the other is a test logic error. Here's the detailed analysis and solutions for each.

---

## Test 1: `test_diferente_seed_diferentes_resultados`

### Why It's Failing

**Root Cause:** The bootstrap produces **identical results** regardless of seed because the test data has **zero residuals**.

**Technical Details:**
```
Result with seed=42:  reserva_total = 2061.8534243534236
Result with seed=123: reserva_total = 2061.8534243534236
Standard deviation:   4.547E-13 (essentially 0)
All percentiles:      2061.8534243534236 (identical)
```

**The Problem:**
1. Chain Ladder creates a "triangulo_ajustado" (fitted values) from the original triangle
2. Residuals = (observed - fitted) / sqrt(fitted)
3. **If fitted values = observed values exactly**, then residuals = 0
4. Resampling zeros produces zeros → all simulations identical
5. Different seeds have no effect because there's no randomness to sample from

**Evidence:**
The test triangle (`triangulo_simple`) produces a perfect Chain Ladder fit, resulting in zero variation. Bootstrap only works when there's actual variation in the residuals.

---

### Solutions for Test 1

#### **Option A: Fix the Test Data (Recommended)**
Add realistic noise to the test triangle so residuals aren't zero.

**Pros:**
- Tests the bootstrap algorithm properly
- Reflects real-world data (always has noise)
- No algorithm changes needed

**Cons:**
- Requires creating new test data

**Implementation:**
```python
# In test fixture
@pytest.fixture
def triangulo_con_ruido():
    """Triángulo con ruido realista para probar bootstrap"""
    np.random.seed(42)  # For reproducible test data
    data = {
        0: [1000, 1200, 1100, 1300, 1250],
        1: [1500, 1800, 1650, 1950, np.nan],
        2: [1800, 2100, 1950, np.nan, np.nan],
        3: [1950, 2250, np.nan, np.nan, np.nan],
        4: [2000, np.nan, np.nan, np.nan, np.nan]
    }
    df = pd.DataFrame(data, index=[2020, 2021, 2022, 2023, 2024])

    # Add realistic noise (±5% random variation)
    for i in range(len(df)):
        for j in range(df.shape[1]):
            if pd.notna(df.iloc[i, j]):
                noise = np.random.normal(0, df.iloc[i, j] * 0.05)
                df.iloc[i, j] += noise

    return df

def test_diferente_seed_diferentes_resultados(self, triangulo_con_ruido):
    """Diferente seed debe producir diferentes resultados"""
    config1 = ConfiguracionBootstrap(num_simulaciones=100, seed=42)
    config2 = ConfiguracionBootstrap(num_simulaciones=100, seed=123)

    bs1 = Bootstrap(config1)
    bs2 = Bootstrap(config2)

    resultado1 = bs1.calcular(triangulo_con_ruido)
    resultado2 = bs2.calcular(triangulo_con_ruido)

    # Now they WILL be different
    assert abs(resultado1.reserva_total - resultado2.reserva_total) > Decimal("0.01")
```

---

#### **Option B: Add Synthetic Noise to Bootstrap Algorithm**
Modify the bootstrap to add artificial noise even when residuals are zero.

**Pros:**
- Works with any data (including perfect fits)
- Handles edge cases automatically

**Cons:**
- Changes the algorithm
- Less statistically pure
- Not standard bootstrap practice

**Implementation:**
```python
# In bootstrap.py - generar_triangulo_sintetico()

# After line 163: residuales_validos = residuales_validos[~np.isnan(residuales_validos)]

# Check if all residuals are near-zero
if len(residuales_validos) == 0 or np.std(residuales_validos) < 1e-10:
    # Add synthetic noise for variation
    # Use Poisson-based noise: variance = mean
    for i in range(len(triangulo_ajustado)):
        for j in range(triangulo_ajustado.shape[1]):
            esp = triangulo_ajustado.iloc[i, j]
            if pd.notna(esp) and esp > 0:
                # Poisson-distributed noise
                noise = np.random.poisson(esp) - esp
                valor_sintetico = esp + noise
                valor_sintetico = max(0, valor_sintetico)
                triangulo_sintetico.iloc[i, j] = valor_sintetico

    return triangulo_sintetico

# Continue with normal resampling...
```

---

#### **Option C: Skip Test When No Variation**
Make the test conditional on having actual residual variation.

**Pros:**
- Honest about what bootstrap can/can't do
- No algorithm changes
- Documents limitation

**Cons:**
- Reduces test coverage
- Doesn't test edge case

**Implementation:**
```python
def test_diferente_seed_diferentes_resultados(self, triangulo_simple):
    """Diferente seed debe producir diferentes resultados"""
    config1 = ConfiguracionBootstrap(num_simulaciones=100, seed=42)
    bs1 = Bootstrap(config1)
    resultado1 = bs1.calcular(triangulo_simple)

    # Check if there's actual variation in the bootstrap
    std_dev = Decimal(resultado1.detalles.get('desviacion_estandar', '0'))

    if std_dev < Decimal('0.01'):
        pytest.skip(
            "Triángulo tiene ajuste perfecto - sin variación para bootstrap. "
            "Esto es esperado para datos sintéticos sin ruido."
        )

    # Only test seed differences if there's variation
    config2 = ConfiguracionBootstrap(num_simulaciones=100, seed=123)
    bs2 = Bootstrap(config2)
    resultado2 = bs2.calcular(triangulo_simple)

    assert abs(resultado1.reserva_total - resultado2.reserva_total) > Decimal("0.01")
```

---

## Recommendation for Test 1

**Use Option A** (Fix the Test Data). This is the cleanest solution because:
1. Bootstrap is designed for real-world data with variation
2. Test data should be realistic
3. No algorithm changes needed
4. Properly tests the seed mechanism

---

## Test 2: `test_calcular_var`

### Why It's Failing

**Root Cause:** The test has a **logic error** - it compares apples to oranges.

**The Bug:**
```python
var_95 = bs.calcular_var(nivel_confianza=0.95)  # Returns: 2061.85 pesos
assert abs(var_95 - bs.config.percentiles[-1]) < Decimal("1000")
#               ^                          ^
#          VaR VALUE               PERCENTILE LEVEL
#        (2061.85 pesos)                (99)
```

**What's Happening:**
- `var_95` = 2061.85 (the 95th percentile VALUE of reserves in pesos)
- `bs.config.percentiles[-1]` = 99 (the LEVEL of the last percentile in the config)
- Comparing 2061.85 - 99 = 1962.85 > 1000 ❌

**What It SHOULD Compare:**
- `var_95` should be compared to `resultado.percentiles[95]`
- Both would be in pesos and comparable

---

### Solutions for Test 2

#### **Option A: Fix Test Assertion (Recommended)**
Compare VaR to the actual percentile value from results.

**Implementation:**
```python
def test_calcular_var(self, triangulo_simple, config_100_sims):
    """Debe calcular VaR al 95%"""
    bs = Bootstrap(config_100_sims)
    resultado = bs.calcular(triangulo_simple)

    var_95 = bs.calcular_var(nivel_confianza=0.95)

    # VaR debe ser positivo
    assert var_95 >= Decimal("0")

    # VaR al 95% debe ser igual al percentil 95 del resultado
    # (pueden diferir ligeramente por redondeo/interpolación)
    percentil_95_resultado = resultado.percentiles.get(95, resultado.percentiles.get(99))
    assert abs(var_95 - percentil_95_resultado) < Decimal("1")
```

---

#### **Option B: More Comprehensive VaR Test**
Test multiple properties of VaR instead of just comparing to percentile.

**Implementation:**
```python
def test_calcular_var(self, triangulo_simple, config_100_sims):
    """Debe calcular VaR correctamente"""
    bs = Bootstrap(config_100_sims)
    resultado = bs.calcular(triangulo_simple)

    # Test VaR at different confidence levels
    var_50 = bs.calcular_var(nivel_confianza=0.50)
    var_95 = bs.calcular_var(nivel_confianza=0.95)
    var_99 = bs.calcular_var(nivel_confianza=0.99)

    # Properties that VaR must satisfy:
    # 1. All VaR values must be non-negative
    assert var_50 >= Decimal("0")
    assert var_95 >= Decimal("0")
    assert var_99 >= Decimal("0")

    # 2. VaR increases with confidence level
    assert var_95 >= var_50, "VaR95 debe ser >= VaR50"
    assert var_99 >= var_95, "VaR99 debe ser >= VaR95"

    # 3. VaR should be close to median for 50%
    assert abs(var_50 - resultado.reserva_total) < Decimal("100")

    # 4. VaR should be within simulation range
    assert var_95 >= Decimal(resultado.detalles['minimo'])
    assert var_95 <= Decimal(resultado.detalles['maximo'])
```

---

#### **Option C: Fix and Document the Percentiles**
Clarify what percentiles represent and test accordingly.

**Implementation:**
```python
def test_calcular_var(self, triangulo_simple, config_100_sims):
    """Debe calcular VaR al 95%"""
    bs = Bootstrap(config_100_sims)
    resultado = bs.calcular(triangulo_simple)

    var_95 = bs.calcular_var(nivel_confianza=0.95)

    # VaR debe ser positivo
    assert var_95 >= Decimal("0")

    # VaR debe coincidir con el percentil 95 almacenado en resultados
    # config.percentiles = [50, 75, 90, 95, 99] son los NIVELES
    # resultado.percentiles = {50: value, 75: value, ...} son los VALORES
    assert 95 in resultado.percentiles, "Percentil 95 debe estar en resultados"

    # VaR(95%) == Percentil 95
    assert abs(var_95 - resultado.percentiles[95]) < Decimal("0.01")
```

---

## Recommendation for Test 2

**Use Option A** (Fix Test Assertion). This is the simplest fix:
- Corrects the obvious bug
- Maintains test intent
- Minimal changes

Optionally combine with **Option B** for more comprehensive VaR testing.

---

## Summary Table

| Test | Issue Type | Severity | Recommended Fix | Effort |
|------|-----------|----------|----------------|--------|
| test_diferente_seed | Bootstrap algorithm limitation | Medium | Option A: Fix test data | Low |
| test_calcular_var | Test logic error | Low | Option A: Fix assertion | Very Low |

---

## Implementation Plan

If you want me to implement the fixes:

1. **For test_diferente_seed:**
   - Create new fixture `triangulo_con_ruido` with realistic noise
   - Update test to use noisy data
   - Document why noise is needed

2. **For test_calcular_var:**
   - Fix assertion to compare `var_95` with `resultado.percentiles[95]`
   - Add comment explaining percentiles vs percentile levels
   - Optionally add more comprehensive VaR property tests

**Expected Result:** 307/307 tests passing (100%)

Would you like me to implement these fixes?
