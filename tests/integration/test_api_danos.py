"""Integration tests for the danos (P&C) API endpoints."""


class TestAutoCalcuar:
    def test_success(self, api_client):
        payload = {
            "valor_vehiculo": 350_000,
            "tipo_vehiculo": "sedan_compacto",
            "antiguedad_anos": 3,
            "zona": "guadalajara",
            "edad_conductor": 35,
            "deducible_pct": 0.05,
        }
        response = api_client.post("/api/v1/danos/auto/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "vehiculo" in data
        assert "conductor" in data
        assert "coberturas" in data
        assert "prima_total" in data
        assert isinstance(data["prima_total"], (int, float))
        assert data["prima_total"] > 0

    def test_success_with_historial(self, api_client):
        payload = {
            "valor_vehiculo": 350_000,
            "tipo_vehiculo": "sedan_compacto",
            "antiguedad_anos": 3,
            "zona": "guadalajara",
            "edad_conductor": 35,
            "historial_siniestros": [0, 0, 1],
        }
        response = api_client.post("/api/v1/danos/auto/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "bonus_malus" in data

    def test_validation_error_negative_valor(self, api_client):
        payload = {
            "valor_vehiculo": -1,
            "tipo_vehiculo": "sedan_compacto",
            "antiguedad_anos": 3,
            "zona": "guadalajara",
            "edad_conductor": 35,
        }
        response = api_client.post("/api/v1/danos/auto/calcular", json=payload)
        assert response.status_code == 422

    def test_validation_error_edad_conductor_under_18(self, api_client):
        payload = {
            "valor_vehiculo": 350_000,
            "tipo_vehiculo": "sedan_compacto",
            "antiguedad_anos": 3,
            "zona": "guadalajara",
            "edad_conductor": 16,
        }
        response = api_client.post("/api/v1/danos/auto/calcular", json=payload)
        assert response.status_code == 422


class TestIncendioCalcular:
    def test_success(self, api_client):
        payload = {
            "valor_inmueble": 5_000_000,
            "tipo_construccion": "concreto",
            "zona": "urbana_media",
            "uso": "habitacional",
        }
        response = api_client.post("/api/v1/danos/incendio/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "valor_inmueble" in data
        assert "prima_anual" in data
        assert "tasa_base" in data
        assert isinstance(data["prima_anual"], (int, float))
        assert data["prima_anual"] > 0

    def test_validation_error_zero_valor(self, api_client):
        payload = {
            "valor_inmueble": 0,
            "tipo_construccion": "concreto",
            "zona": "urbana_media",
            "uso": "habitacional",
        }
        response = api_client.post("/api/v1/danos/incendio/calcular", json=payload)
        assert response.status_code == 422


class TestRCCalcular:
    def test_success(self, api_client):
        payload = {
            "limite_responsabilidad": 10_000_000,
            "deducible": 100_000,
            "clase_actividad": "oficinas",
        }
        response = api_client.post("/api/v1/danos/rc/calcular", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "limite_responsabilidad" in data
        assert "prima_anual" in data
        assert "tasa_base" in data
        assert isinstance(data["prima_anual"], (int, float))


class TestBonusMalus:
    def test_success_no_claims(self, api_client):
        payload = {
            "nivel_actual": 0,
            "numero_siniestros": 0,
        }
        response = api_client.post("/api/v1/danos/bonus-malus", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "nivel_previo" in data
        assert "nivel_nuevo" in data
        assert "factor" in data
        assert data["nivel_previo"] == 0
        # No claims should decrease the level
        assert data["nivel_nuevo"] < data["nivel_previo"]

    def test_success_with_claims(self, api_client):
        payload = {
            "nivel_actual": 0,
            "numero_siniestros": 2,
        }
        response = api_client.post("/api/v1/danos/bonus-malus", json=payload)
        assert response.status_code == 200
        data = response.json()
        # Claims should increase the level
        assert data["nivel_nuevo"] > data["nivel_previo"]


class TestFrecuenciaSeveridad:
    def test_success_with_seed(self, api_client):
        payload = {
            "dist_frecuencia": "poisson",
            "params_frecuencia": {"lambda_": 5.0},
            "dist_severidad": "lognormal",
            "params_severidad": {"mu": 10.0, "sigma": 1.5},
            "n_simulaciones": 10_000,
            "seed": 42,
        }
        response = api_client.post("/api/v1/danos/frecuencia-severidad", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "prima_pura" in data
        assert "var_95" in data
        assert "tvar_95" in data
        assert "var_99" in data
        assert "tvar_99" in data
        assert "simulaciones" in data
        assert isinstance(data["prima_pura"], (int, float))
        assert data["prima_pura"] > 0

    def test_deterministic_with_same_seed(self, api_client):
        payload = {
            "dist_frecuencia": "poisson",
            "params_frecuencia": {"lambda_": 5.0},
            "dist_severidad": "lognormal",
            "params_severidad": {"mu": 10.0, "sigma": 1.5},
            "n_simulaciones": 10_000,
            "seed": 123,
        }
        r1 = api_client.post("/api/v1/danos/frecuencia-severidad", json=payload)
        r2 = api_client.post("/api/v1/danos/frecuencia-severidad", json=payload)
        assert r1.json()["prima_pura"] == r2.json()["prima_pura"]


class TestDanosProcedencia:
    """Las cotizaciones de daños deben viajar con su alcance y su respaldo.

    El aviso de `tablas_amis` existia como constante y no lo importaba nadie, e
    incendio y RC no tenian ninguno: una prima calculada con tasas ilustrativas
    cruzaba HTTP sin señal de serlo.
    """

    def test_auto_incluye_aviso_y_nivel_de_respaldo(self, api_client):
        from suite_actuarial.danos.auto import DISCLAIMER, VALIDATION_TIER

        payload = {
            "valor_vehiculo": 350_000,
            "tipo_vehiculo": "sedan_compacto",
            "antiguedad_anos": 3,
            "zona": "guadalajara",
            "edad_conductor": 35,
        }
        response = api_client.post("/api/v1/danos/auto/calcular", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["disclaimer"] == DISCLAIMER
        assert data["disclaimer"].strip()
        assert "ILUSTRATIVOS" in data["disclaimer"]
        # El limite propio del producto, no solo el de las tablas.
        assert "responsabilidad civil" in data["disclaimer"]
        assert data["validation_tier"] == VALIDATION_TIER == "experimental"

    def test_incendio_incluye_aviso_y_nivel_de_respaldo(self, api_client):
        from suite_actuarial.danos.incendio import DISCLAIMER, VALIDATION_TIER

        payload = {
            "valor_inmueble": 5_000_000,
            "tipo_construccion": "concreto",
            "zona": "urbana_media",
            "uso": "habitacional",
        }
        response = api_client.post("/api/v1/danos/incendio/calcular", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["disclaimer"] == DISCLAIMER
        assert data["disclaimer"].strip()
        assert "ILUSTRATIVOS" in data["disclaimer"]
        assert data["validation_tier"] == VALIDATION_TIER == "experimental"

    def test_rc_incluye_aviso_y_nivel_de_respaldo(self, api_client):
        from suite_actuarial.danos.rc import DISCLAIMER, VALIDATION_TIER

        payload = {
            "limite_responsabilidad": 10_000_000,
            "deducible": 100_000,
            "clase_actividad": "oficinas",
        }
        response = api_client.post("/api/v1/danos/rc/calcular", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["disclaimer"] == DISCLAIMER
        assert data["disclaimer"].strip()
        assert "ILUSTRATIVOS" in data["disclaimer"]
        assert data["validation_tier"] == VALIDATION_TIER == "experimental"

    def test_bonus_malus_incluye_aviso_y_nivel_de_respaldo(self, api_client):
        """La escala BMS no procede de tarifa alguna y el factor lo declara."""
        from suite_actuarial.danos.tarifas import DISCLAIMER, VALIDATION_TIER

        payload = {"nivel_actual": 0, "numero_siniestros": 0}
        response = api_client.post("/api/v1/danos/bonus-malus", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["disclaimer"] == DISCLAIMER
        assert data["disclaimer"].strip()
        assert "ILUSTRATIVA" in data["disclaimer"]
        # El aviso nombra el limite que la respuesta no puede mostrar: la escala
        # no esta calibrada para compensar descuentos con recargos.
        assert "calibrada" in data["disclaimer"]
        assert data["validation_tier"] == VALIDATION_TIER == "experimental"

    def test_frecuencia_severidad_incluye_aviso_y_nivel_de_respaldo(self, api_client):
        """El metodo es estandar; los parametros no se ajustan a dato alguno."""
        from suite_actuarial.danos.frecuencia_severidad import DISCLAIMER, VALIDATION_TIER

        payload = {
            "dist_frecuencia": "poisson",
            "params_frecuencia": {"lambda_": 5.0},
            "dist_severidad": "lognormal",
            "params_severidad": {"mu": 10.0, "sigma": 1.5},
            "n_simulaciones": 1_000,
            "seed": 42,
        }
        response = api_client.post("/api/v1/danos/frecuencia-severidad", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["disclaimer"] == DISCLAIMER
        assert data["disclaimer"].strip()
        assert "ILUSTRATIVAS" in data["disclaimer"]
        # Los dos limites propios de esta respuesta: no ajusta a datos y sus
        # medidas de cola son estimaciones Monte Carlo sin error reportado.
        assert "no ajusta ninguna distribucion a datos" in data["disclaimer"]
        assert "Monte Carlo" in data["disclaimer"]
        assert data["validation_tier"] == VALIDATION_TIER == "experimental"


class TestFrecuenciaSeveridadParametros:
    """Un nombre de parametro equivocado devolvia 500 con traceback.

    Las distribuciones se construyen indexando el diccionario recibido, asi que
    `{"lambda": 5.0}` en vez de `{"lambda_": 5.0}` reventaba como `KeyError`
    dentro del modelo y salia como error interno. El contrato dice justo lo
    contrario: preservar el error util y no exponer el traceback.
    """

    BASE = {
        "dist_frecuencia": "poisson",
        "params_frecuencia": {"lambda_": 5.0},
        "dist_severidad": "lognormal",
        "params_severidad": {"mu": 10.0, "sigma": 1.5},
        "n_simulaciones": 1_000,
        "seed": 42,
    }

    def test_parametro_de_frecuencia_no_reconocido_es_422_que_nombra_el_valido(self, api_client):
        payload = {**self.BASE, "params_frecuencia": {"lambda": 5.0}}
        response = api_client.post("/api/v1/danos/frecuencia-severidad", json=payload)

        assert response.status_code == 422
        detalle = str(response.json()["detail"])
        assert "lambda_" in detalle
        assert "no se reconocen" in detalle
        # Nada del interior del servicio viaja en la respuesta.
        assert "Traceback" not in detalle
        assert "KeyError" not in detalle

    def test_parametro_de_severidad_ausente_es_422_que_nombra_el_juego(self, api_client):
        payload = {
            **self.BASE,
            "dist_severidad": "pareto",
            "params_severidad": {"alpha": 2.5},
        }
        response = api_client.post("/api/v1/danos/frecuencia-severidad", json=payload)

        assert response.status_code == 422
        detalle = str(response.json()["detail"])
        assert "faltan" in detalle
        assert "scale" in detalle
        assert "alpha" in detalle

    def test_la_distribucion_desconocida_sigue_siendo_400_del_dominio(self, api_client):
        """Asimetria deliberada: el nombre de la distribucion lo valida el dominio.

        Sin juego de parametros contra el cual comparar, el borde HTTP no puede
        decir nada util; `ModeloColectivo` sí, y lista sus opciones.
        """
        payload = {**self.BASE, "dist_frecuencia": "cauchy"}
        response = api_client.post("/api/v1/danos/frecuencia-severidad", json=payload)

        assert response.status_code == 400
        assert "no soportada" in response.json()["detail"]
        assert "poisson" in response.json()["detail"]

    def test_el_juego_correcto_de_parametros_sigue_pasando(self, api_client):
        response = api_client.post("/api/v1/danos/frecuencia-severidad", json=self.BASE)
        assert response.status_code == 200
        assert response.json()["prima_pura"] > 0
