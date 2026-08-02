"""Integration tests for the regulatory API endpoints."""

import pytest

VALID_RCS_PAYLOAD = {
    "config_vida": {
        "suma_asegurada_total": 50_000_000,
        "reserva_matematica": 15_000_000,
        "edad_promedio_asegurados": 40,
        "duracion_promedio_polizas": 10,
        "numero_asegurados": 1000,
    },
    "config_danos": {
        "primas_retenidas_12m": 20_000_000,
        "reserva_siniestros": 8_000_000,
        "coeficiente_variacion": 0.15,
        "numero_ramos": 3,
    },
    "config_inversion": {
        "valor_acciones": 10_000_000,
        "valor_bonos_gubernamentales": 30_000_000,
        "valor_bonos_corporativos": 15_000_000,
        "valor_inmuebles": 5_000_000,
        "duracion_promedio_bonos": 5.0,
        "calificacion_promedio_bonos": "AA",
    },
    "capital_minimo_pagado": 100_000_000,
}


class TestRCS:
    def test_success(self, api_client):
        response = api_client.post("/api/v1/regulatory/rcs", json=VALID_RCS_PAYLOAD)
        assert response.status_code == 200
        data = response.json()
        assert "rcs_total" in data
        assert "cumple_regulacion" in data
        assert "ratio_solvencia" in data
        assert isinstance(data["rcs_total"], (int, float))
        assert isinstance(data["cumple_regulacion"], bool)
        assert "desglose_por_riesgo" in data

        # The public contract is capital available / RCS, not its inverse.
        assert data["ratio_solvencia"] == pytest.approx(
            VALID_RCS_PAYLOAD["capital_minimo_pagado"] / data["rcs_total"]
        )
        assert data["ratio_solvencia"] > 1

    def test_ratio_solvencia_escala_con_el_capital(self, api_client):
        """Duplicar el capital debe duplicar el ratio.

        Oraculo de orientacion independiente de magnitudes: bajo la definicion
        correcta (capital / RCS) el ratio es proporcional al capital; bajo la
        definicion invertida (RCS / capital) se reduciria a la mitad. El RCS no
        depende del capital, asi que la comparacion aisla la orientacion.
        """
        base = api_client.post("/api/v1/regulatory/rcs", json=VALID_RCS_PAYLOAD).json()
        doble = api_client.post(
            "/api/v1/regulatory/rcs",
            json={**VALID_RCS_PAYLOAD, "capital_minimo_pagado": 200_000_000},
        ).json()

        assert doble["rcs_total"] == pytest.approx(base["rcs_total"])
        assert doble["ratio_solvencia"] == pytest.approx(2 * base["ratio_solvencia"], rel=1e-6)

    def test_ratio_solvencia_frontera_capital_igual_rcs(self, api_client):
        """Con capital exactamente igual al RCS el ratio es 1.0 y hay cumplimiento.

        Se toma el `rcs_total` de una primera respuesta y se reenvia como
        capital: la frontera regulatoria (100% de cobertura) queda fijada sin
        reproducir ninguna formula del paquete.
        """
        base = api_client.post("/api/v1/regulatory/rcs", json=VALID_RCS_PAYLOAD).json()

        response = api_client.post(
            "/api/v1/regulatory/rcs",
            json={**VALID_RCS_PAYLOAD, "capital_minimo_pagado": base["rcs_total"]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ratio_solvencia"] == pytest.approx(1.0, rel=1e-6)
        assert data["cumple_regulacion"] is True
        assert data["excedente_solvencia"] == pytest.approx(0.0, abs=1.0)

    def test_ratio_solvencia_insuficiente_es_menor_que_uno(self, api_client):
        """Una aseguradora con la mitad del capital requerido reporta ratio < 1."""
        base = api_client.post("/api/v1/regulatory/rcs", json=VALID_RCS_PAYLOAD).json()

        data = api_client.post(
            "/api/v1/regulatory/rcs",
            json={**VALID_RCS_PAYLOAD, "capital_minimo_pagado": base["rcs_total"] / 2},
        ).json()
        assert data["ratio_solvencia"] == pytest.approx(0.5, rel=1e-6)
        assert data["cumple_regulacion"] is False
        assert data["excedente_solvencia"] < 0

    def test_validation_error_zero_capital(self, api_client):
        """Capital cero no tiene ratio definido: se rechaza en la frontera."""
        payload = {**VALID_RCS_PAYLOAD, "capital_minimo_pagado": 0}
        response = api_client.post("/api/v1/regulatory/rcs", json=payload)
        assert response.status_code == 422

    def test_success_vida_only(self, api_client):
        payload = {
            "config_vida": VALID_RCS_PAYLOAD["config_vida"],
            "capital_minimo_pagado": 50_000_000,
        }
        response = api_client.post("/api/v1/regulatory/rcs", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["rcs_suscripcion_vida"] >= 0
        assert data["rcs_suscripcion_danos"] == 0

    def test_validation_error_missing_capital(self, api_client):
        payload = {"config_vida": VALID_RCS_PAYLOAD["config_vida"]}
        response = api_client.post("/api/v1/regulatory/rcs", json=payload)
        assert response.status_code == 422

    def test_validation_error_negative_capital(self, api_client):
        payload = {**VALID_RCS_PAYLOAD, "capital_minimo_pagado": -1}
        response = api_client.post("/api/v1/regulatory/rcs", json=payload)
        assert response.status_code == 422


class TestRCSProcedencia:
    """El RCS debe viajar con la advertencia de su alcance y su procedencia."""

    def test_respuesta_incluye_el_aviso_y_el_perfil(self, api_client):
        """El aviso existia solo como UserWarning de Python; nunca cruzaba HTTP."""
        from suite_actuarial.config.loader import config_vigente

        response = api_client.post("/api/v1/regulatory/rcs", json=VALID_RCS_PAYLOAD)

        assert response.status_code == 200
        data = response.json()
        assert "aproximaciones pedagogicas" in data["disclaimer"]
        assert data["anio_regulatorio"] == config_vigente().anio
        assert data["validation_tier"]
        assert set(data["correlaciones_aplicadas"]) == {
            "vida_danos",
            "vida_inversion",
            "danos_inversion",
        }

    def test_sin_ningun_riesgo_configurado_se_rechaza(self, api_client):
        """Antes devolvia rcs_total=0 con cumple_regulacion=True."""
        payload = {"capital_minimo_pagado": 100_000_000}
        response = api_client.post("/api/v1/regulatory/rcs", json=payload)

        assert response.status_code == 400


class TestSATDeductibility:
    def test_success(self, api_client):
        payload = {
            "tipo_seguro": "vida",
            "monto_prima": 50_000,
            "es_persona_fisica": True,
            "uma_anual": 39960.60,
        }
        response = api_client.post("/api/v1/regulatory/sat/deductibility", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "es_deducible" in data
        assert "monto_deducible" in data
        assert "fundamento_legal" in data
        assert isinstance(data["es_deducible"], bool)

    def test_validation_error_zero_prima(self, api_client):
        payload = {
            "tipo_seguro": "vida",
            "monto_prima": 0,
        }
        response = api_client.post("/api/v1/regulatory/sat/deductibility", json=payload)
        assert response.status_code == 422

    def test_uma_omitida_toma_la_del_perfil_vigente(self, api_client):
        """Sin `uma_anual` el endpoint usa el perfil versionado, no una constante.

        El valor esperado se lee del propio perfil regulatorio, que es la unica
        fuente de verdad del año; antes el router llevaba un literal fijo que no
        correspondia a ningun año publicado.
        """
        from suite_actuarial.config.loader import config_vigente

        perfil = config_vigente()
        payload = {
            "tipo_seguro": "pensiones",
            "monto_prima": 50_000,
            "es_persona_fisica": True,
        }
        response = api_client.post("/api/v1/regulatory/sat/deductibility", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["uma_anual_aplicada"] == pytest.approx(float(perfil.uma.uma_anual))
        assert data["anio_regulatorio"] == perfil.anio

    def test_estado_indeterminado_se_expone(self, api_client):
        """Faltando insumos, la respuesta lo dice en vez de fingir certeza."""
        payload = {
            "tipo_seguro": "gastos_medicos",
            "monto_prima": 50_000,
            "es_persona_fisica": True,
        }
        response = api_client.post("/api/v1/regulatory/sat/deductibility", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["estado"] == "indeterminate"
        assert "metodo_pago" in data["factores_faltantes"]


class TestSATTopeGlobalArt151:
    """El tope del último párrafo del Art. 151 LISR cruza el contrato HTTP.

    Las cifras esperadas se calculan a mano desde el estatuto y la UMA anual
    que la propia petición envía, no desde la respuesta:

        uma_anual = 42,794.64  ->  5 UMA = 213,973.20
    """

    def test_gmm_con_ingresos_totales_aplica_el_tope(self, api_client):
        """15% x 300,000 = 45,000 < 5 UMA: el tope recorta la prima de 50,000."""
        payload = {
            "tipo_seguro": "gastos_medicos",
            "monto_prima": 50_000,
            "es_persona_fisica": True,
            "uma_anual": 42_794.64,
            "ingresos_totales_anuales": 300_000,
            "metodo_pago": "transferencia",
        }
        response = api_client.post("/api/v1/regulatory/sat/deductibility", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["monto_deducible"] == pytest.approx(45_000.0)
        assert data["tope_global"] == "aplicado"
        assert data["estado"] == "eligible"

    def test_gmm_sin_ingresos_totales_declara_el_tope_no_determinado(self, api_client):
        """Sin el ingreso total, la respuesta no finge un 100% deducible.

        Se aplica solo la rama de 5 UMA (213,973.20), por debajo de la prima de
        400,000, y la respuesta nombra el dato que falta.
        """
        payload = {
            "tipo_seguro": "gastos_medicos",
            "monto_prima": 400_000,
            "es_persona_fisica": True,
            "uma_anual": 42_794.64,
            "metodo_pago": "transferencia",
        }
        response = api_client.post("/api/v1/regulatory/sat/deductibility", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["monto_deducible"] == pytest.approx(213_973.20)
        assert data["tope_global"] == "parcial_sin_ingresos"
        assert data["estado"] == "indeterminate"
        assert "ingresos_totales_anuales" in data["factores_faltantes"]
        assert "15%" in data["nota_tope_global"]

    def test_pensiones_queda_fuera_del_tope_global(self, api_client):
        """La fracción V está excluida del tope global por el propio párrafo.

        10% x 1,000,000 = 100,000 < 5 UMA: manda el tope propio de la fracción.
        """
        payload = {
            "tipo_seguro": "pensiones",
            "monto_prima": 150_000,
            "es_persona_fisica": True,
            "uma_anual": 42_794.64,
            "ingreso_anual": 1_000_000,
            "metodo_pago": "transferencia",
        }
        response = api_client.post("/api/v1/regulatory/sat/deductibility", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["monto_deducible"] == pytest.approx(100_000.0)
        assert data["tope_global"] == "no_aplicable"
        assert "fracc. VI" not in data["fundamento_legal"]


class TestSinPerfilVigente:
    """Sin perfil vigente para la fecha del servidor, los endpoints se caen bien.

    El agregador de RCS leía los factores CNSF del perfil vigente dentro de
    `__init__`, y el router solo atrapaba `ValueError` y `TypeError`: al agotarse
    la cobertura de perfiles el endpoint devolvía 500 con un traceback. Ahora
    devuelve 503, porque el input del cliente es válido y quien no puede
    responder es el servidor, y el detalle nombra el rango cubierto.
    """

    @pytest.fixture
    def hoy_sin_cobertura(self, monkeypatch):
        from datetime import date

        from suite_actuarial.config import loader

        monkeypatch.setattr(loader, "_hoy", lambda: date(2030, 6, 15))

    def test_rcs_devuelve_503_con_el_rango(self, api_client, hoy_sin_cobertura):
        response = api_client.post("/api/v1/regulatory/rcs", json=VALID_RCS_PAYLOAD)

        assert response.status_code == 503
        detalle = response.json()["detail"]
        assert "2030-06-15" in detalle
        assert "2024-02-01 a 2027-01-31" in detalle

    def test_deducibilidad_devuelve_503(self, api_client, hoy_sin_cobertura):
        payload = {
            "tipo_seguro": "gastos_medicos",
            "monto_prima": 50_000,
            "es_persona_fisica": True,
        }
        response = api_client.post("/api/v1/regulatory/sat/deductibility", json=payload)

        assert response.status_code == 503
        assert "2024-02-01 a 2027-01-31" in response.json()["detail"]

    def test_retenciones_devuelve_503(self, api_client, hoy_sin_cobertura):
        payload = {
            "tipo_seguro": "vida",
            "monto_pago": 100_000,
            "monto_gravable": 50_000,
        }
        response = api_client.post("/api/v1/regulatory/sat/withholding", json=payload)

        assert response.status_code == 503
        assert "2024-02-01 a 2027-01-31" in response.json()["detail"]


class TestSATWithholding:
    def test_success(self, api_client):
        payload = {
            "tipo_seguro": "vida",
            "monto_pago": 100_000,
            "monto_gravable": 50_000,
            "es_renta_vitalicia": False,
            "es_retiro_ahorro": False,
        }
        response = api_client.post("/api/v1/regulatory/sat/withholding", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "requiere_retencion" in data
        assert "monto_retencion" in data
        assert "monto_neto_pagar" in data
        assert isinstance(data["requiere_retencion"], bool)

    def test_validation_error_missing_tipo(self, api_client):
        payload = {
            "monto_pago": 100_000,
            "monto_gravable": 50_000,
        }
        response = api_client.post("/api/v1/regulatory/sat/withholding", json=payload)
        assert response.status_code == 422

    def test_renta_vitalicia_y_retiro_a_la_vez_se_rechaza(self, api_client):
        """Un pago no puede ser las dos cosas; antes devolvia 20% en silencio."""
        payload = {
            "tipo_seguro": "vida",
            "monto_pago": 500_000,
            "monto_gravable": 350_000,
            "es_renta_vitalicia": True,
            "es_retiro_ahorro": True,
        }
        response = api_client.post("/api/v1/regulatory/sat/withholding", json=payload)

        assert response.status_code == 400

    def test_respuesta_declara_la_regla_y_su_limite(self, api_client):
        payload = {
            "tipo_seguro": "vida",
            "monto_pago": 500_000,
            "monto_gravable": 350_000,
            "es_retiro_ahorro": True,
        }
        response = api_client.post("/api/v1/regulatory/sat/withholding", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["regla_aplicada"]
        assert "no estan verificadas" in data["disclaimer"]
