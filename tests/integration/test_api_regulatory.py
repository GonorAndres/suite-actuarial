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
