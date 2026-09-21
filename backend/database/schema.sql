CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS citext;

CREATE TYPE rol_usuario AS ENUM ('cliente', 'asesor', 'aliado', 'admin', 'contabilidad');
CREATE TYPE estado_usuario AS ENUM ('pendiente_verificacion', 'activo', 'bloqueado', 'inactivo');
CREATE TYPE ocupacion_cliente AS ENUM ('empleado', 'independiente', 'pensionado', 'fuerzas_militares');
CREATE TYPE decision_credito AS ENUM ('aprobado', 'rechazado', 'perfil_gris');
CREATE TYPE estado_solicitud AS ENUM ('creada', 'en_evaluacion', 'aprobada', 'rechazada', 'en_revision', 'desembolsada', 'cancelada');
CREATE TYPE tipo_contrato AS ENUM ('indefinido', 'fijo', 'obra_labor', 'no_aplica');
CREATE TYPE estado_otp AS ENUM ('pendiente', 'aprobado', 'expirado', 'fallido');
CREATE TYPE tipo_aliado AS ENUM ('fintech', 'banco', 'cooperativa', 'libranza', 'bnpl', 'otro');
CREATE TYPE tipo_seguro AS ENUM ('vida_decreciente', 'vida_nivelada', 'todo_riesgo', 'desempleo', 'asistencia', 'otro');
CREATE TYPE estado_poliza AS ENUM ('cotizada', 'emitida', 'vigente', 'vencida', 'cancelada', 'siniestrada');
CREATE TYPE tipo_criterio AS ENUM ('buro', 'interno', 'aliado');
CREATE TYPE estado_desembolso AS ENUM ('pendiente', 'confirmado', 'rechazado', 'anulado');
CREATE TYPE tipo_cuenta AS ENUM ('ahorros');

CREATE TABLE ciudad (
    id_ciudad BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL,
    departamento VARCHAR(120) NOT NULL,
    pais VARCHAR(80) NOT NULL DEFAULT 'Colombia',
    CONSTRAINT uq_ciudad UNIQUE (nombre, departamento, pais)
);

CREATE OR REPLACE FUNCTION actualizar_fecha_actualizacion()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    NEW.fecha_actualizacion = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;

CREATE TABLE rol (
    id_rol SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre rol_usuario NOT NULL UNIQUE,
    descripcion VARCHAR(200)
);

CREATE TABLE usuario (
    id_usuario UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    correo CITEXT NOT NULL UNIQUE,
    hash_contrasena TEXT NOT NULL,
    estado estado_usuario NOT NULL DEFAULT 'pendiente_verificacion',
    fecha_verificacion TIMESTAMPTZ,
    fecha_ultimo_acceso TIMESTAMPTZ,
    fecha_ultimo_cambio_password TIMESTAMPTZ,
    requiere_cambio_password BOOLEAN NOT NULL DEFAULT FALSE,
    intentos_fallidos_login SMALLINT NOT NULL DEFAULT 0,
    bloqueado_hasta TIMESTAMPTZ,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_usuario_intentos_login CHECK (intentos_fallidos_login >= 0)
);

CREATE TABLE usuario_rol (
    id_usuario UUID NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_rol SMALLINT NOT NULL REFERENCES rol(id_rol),
    fecha_asignacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario, id_rol)
);

CREATE TABLE archivo_carga (
    id_archivo BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    fecha_carga TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    hash_archivo VARCHAR(128) NOT NULL UNIQUE
);

CREATE TABLE asesor (
    id_asesor BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario UUID NOT NULL UNIQUE REFERENCES usuario(id_usuario),
    nombre VARCHAR(180) NOT NULL,
    telefono VARCHAR(40),
    id_ciudad BIGINT REFERENCES ciudad(id_ciudad)
);

CREATE TABLE concesionario (
    id_concesionario BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nit VARCHAR(30) UNIQUE,
    nombre VARCHAR(180) NOT NULL UNIQUE,
    id_ciudad BIGINT REFERENCES ciudad(id_ciudad)
);

CREATE TABLE aliado_financiero (
    id_aliado BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nit VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(180) NOT NULL UNIQUE,
    tipo tipo_aliado NOT NULL,
    sitio_web VARCHAR(255),
    es_propio BOOLEAN NOT NULL DEFAULT FALSE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE aliado_usuario (
    id_usuario UUID NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_aliado BIGINT NOT NULL REFERENCES aliado_financiero(id_aliado) ON DELETE CASCADE,
    rol_interno VARCHAR(40),
    fecha_asignacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (id_usuario, id_aliado)
);

CREATE TABLE aliado_concesionario (
    id_aliado BIGINT NOT NULL REFERENCES aliado_financiero(id_aliado) ON DELETE CASCADE,
    id_concesionario BIGINT NOT NULL REFERENCES concesionario(id_concesionario) ON DELETE CASCADE,
    comision_pct NUMERIC(8,4),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_inicio DATE,
    fecha_fin DATE,
    PRIMARY KEY (id_aliado, id_concesionario),
    CONSTRAINT ck_aliado_concesionario_comision CHECK (comision_pct IS NULL OR comision_pct BETWEEN 0 AND 100),
    CONSTRAINT ck_aliado_concesionario_fechas CHECK (fecha_fin IS NULL OR fecha_inicio IS NULL OR fecha_fin >= fecha_inicio)
);

CREATE TABLE aliado_producto (
    id_aliado_producto BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_aliado BIGINT NOT NULL REFERENCES aliado_financiero(id_aliado) ON DELETE CASCADE,
    nombre VARCHAR(180) NOT NULL,
    tasa_min NUMERIC(8,4),
    tasa_max NUMERIC(8,4),
    plazo_min_meses SMALLINT,
    plazo_max_meses SMALLINT,
    monto_min NUMERIC(18,2),
    monto_max NUMERIC(18,2),
    cuota_inicial_min_pct NUMERIC(8,4),
    requiere_aval BOOLEAN NOT NULL DEFAULT FALSE,
    score_min SMALLINT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_aliado_producto UNIQUE (id_aliado, nombre),
    CONSTRAINT ck_aliado_producto_plazo CHECK (
        plazo_min_meses IS NULL OR plazo_max_meses IS NULL
        OR plazo_max_meses >= plazo_min_meses
    ),
    CONSTRAINT ck_aliado_producto_monto CHECK (
        monto_min IS NULL OR monto_max IS NULL OR monto_max >= monto_min
    )
);

CREATE TABLE aliado_regla_elegibilidad (
    id_regla BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_aliado_producto BIGINT NOT NULL REFERENCES aliado_producto(id_aliado_producto) ON DELETE CASCADE,
    campo VARCHAR(80) NOT NULL,
    operador VARCHAR(10) NOT NULL,
    valor_json JSONB NOT NULL,
    CONSTRAINT ck_regla_operador CHECK (operador IN ('>=', '<=', '=', '!=', 'IN', 'NOT IN'))
);

CREATE TABLE cliente (
    id_cliente BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario UUID UNIQUE REFERENCES usuario(id_usuario),
    tipo_documento VARCHAR(30) NOT NULL,
    num_cedula VARCHAR(40) NOT NULL UNIQUE,
    nombre_completo VARCHAR(200) NOT NULL,
    fecha_expedicion DATE,
    id_ciudad_expedicion BIGINT REFERENCES ciudad(id_ciudad),
    fecha_nacimiento DATE NOT NULL,
    id_ciudad_nacimiento BIGINT REFERENCES ciudad(id_ciudad),
    pais VARCHAR(80) NOT NULL DEFAULT 'Colombia',
    genero VARCHAR(30),
    ocupacion ocupacion_cliente,
    perfil_cliente VARCHAR(30),
    es_persona_natural BOOLEAN NOT NULL DEFAULT TRUE,
    nacionalidad VARCHAR(80) NOT NULL DEFAULT 'Colombia',
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE solicitud_credito (
    id_solicitud UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    num_solicitud BIGINT GENERATED ALWAYS AS IDENTITY UNIQUE,
    id_cliente BIGINT NOT NULL REFERENCES cliente(id_cliente),
    id_asesor BIGINT REFERENCES asesor(id_asesor),
    id_concesionario BIGINT REFERENCES concesionario(id_concesionario),
    id_archivo BIGINT REFERENCES archivo_carga(id_archivo),
    id_aliado_origen BIGINT REFERENCES aliado_financiero(id_aliado),
    fecha_hora TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    moneda CHAR(3) NOT NULL DEFAULT 'COP',
    decision decision_credito,
    estado estado_solicitud NOT NULL DEFAULT 'creada',
    descripcion_estado TEXT,
    codigo_estado_externo VARCHAR(50),
    accion VARCHAR(100),
    fecha_hora_firma TIMESTAMPTZ,
    uuid_firma UUID UNIQUE,
    autenticacion VARCHAR(100),
    CONSTRAINT ck_solicitud_moneda CHECK (moneda ~ '^[A-Z]{3}$')
);

CREATE TABLE solicitud_estado_historial (
    id_historial BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL REFERENCES solicitud_credito(id_solicitud),
    estado_anterior estado_solicitud,
    estado_nuevo estado_solicitud NOT NULL,
    id_usuario_cambio UUID REFERENCES usuario(id_usuario) ON DELETE SET NULL,
    motivo TEXT,
    fecha_hora TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION registrar_cambio_estado()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    usuario_actual UUID;
BEGIN
    IF NEW.estado IS DISTINCT FROM OLD.estado THEN
        usuario_actual = CASE
            WHEN current_setting('app.user_id', TRUE) ~ '^[0-9a-fA-F-]{36}$'
            THEN current_setting('app.user_id', TRUE)::UUID
            ELSE NULL
        END;
        INSERT INTO solicitud_estado_historial (
            id_solicitud,
            estado_anterior,
            estado_nuevo,
            id_usuario_cambio,
            motivo
        )
        VALUES (
            NEW.id_solicitud,
            OLD.estado,
            NEW.estado,
            usuario_actual,
            NEW.descripcion_estado
        );
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_solicitud_estado_historial
AFTER UPDATE OF estado ON solicitud_credito
FOR EACH ROW
EXECUTE FUNCTION registrar_cambio_estado();

CREATE TABLE oferta_credito (
    id_oferta BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    id_aliado_producto BIGINT NOT NULL REFERENCES aliado_producto(id_aliado_producto),
    id_usuario_solicitante UUID REFERENCES usuario(id_usuario) ON DELETE SET NULL,
    elegible BOOLEAN NOT NULL,
    motivo_no_elegible TEXT,
    tasa_ofrecida NUMERIC(8,4),
    plazo_ofrecido INTEGER,
    cuota_mensual NUMERIC(18,2),
    monto_aprobado NUMERIC(18,2),
    comision_aliado NUMERIC(18,2),
    moneda CHAR(3) NOT NULL DEFAULT 'COP',
    seleccionada BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_generacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    version_api VARCHAR(20),
    respuesta_raw JSONB,
    CONSTRAINT uq_oferta_solicitud_aliado UNIQUE (id_solicitud, id_aliado_producto),
    CONSTRAINT ck_oferta_moneda CHECK (moneda ~ '^[A-Z]{3}$'),
    CONSTRAINT ck_oferta_elegible CHECK (
        NOT elegible
        OR (
            tasa_ofrecida IS NOT NULL
            AND monto_aprobado IS NOT NULL
            AND cuota_mensual IS NOT NULL
        )
    )
);

CREATE UNIQUE INDEX uq_oferta_seleccionada
ON oferta_credito (id_solicitud)
WHERE seleccionada = TRUE;

CREATE TABLE solicitud_contacto_vivienda (
    id_contacto_vivienda BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL UNIQUE REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    correo CITEXT,
    telefono VARCHAR(40),
    direccion VARCHAR(250),
    barrio VARCHAR(120),
    id_ciudad BIGINT REFERENCES ciudad(id_ciudad),
    estrato SMALLINT,
    tipo_vivienda VARCHAR(50),
    zona_rural BOOLEAN,
    estado_civil VARCHAR(40),
    personas_a_cargo SMALLINT,
    num_hijos SMALLINT,
    es_cabeza_familia BOOLEAN,
    cuenta_bienes_raices BOOLEAN,
    cuenta_vehiculo BOOLEAN,
    tiene_moto BOOLEAN,
    tiene_carro BOOLEAN,
    primera_moto BOOLEAN,
    estoy_financiando BOOLEAN,
    CONSTRAINT ck_contacto_estrato CHECK (estrato IS NULL OR estrato BETWEEN 0 AND 6),
    CONSTRAINT ck_contacto_dependientes CHECK (personas_a_cargo IS NULL OR personas_a_cargo >= 0),
    CONSTRAINT ck_contacto_hijos CHECK (num_hijos IS NULL OR num_hijos >= 0)
);

CREATE TABLE datos_laborales (
    id_datos_laborales BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL UNIQUE REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    tipo_contrato tipo_contrato,
    meses_continuidad INTEGER,
    anos_camara_comercio NUMERIC(6,2),
    ingreso_mensual NUMERIC(18,2),
    otros_ingresos NUMERIC(18,2) NOT NULL DEFAULT 0,
    nombre_empresa VARCHAR(200),
    id_ciudad_empresa BIGINT REFERENCES ciudad(id_ciudad),
    fecha_ingreso DATE,
    nivel_educativo VARCHAR(100),
    profesion VARCHAR(120),
    cargo VARCHAR(120),
    actividad_comercial VARCHAR(180),
    CONSTRAINT ck_laboral_meses CHECK (meses_continuidad IS NULL OR meses_continuidad >= 0),
    CONSTRAINT ck_laboral_camara CHECK (anos_camara_comercio IS NULL OR anos_camara_comercio >= 0),
    CONSTRAINT ck_laboral_ingreso CHECK (ingreso_mensual IS NULL OR ingreso_mensual >= 0),
    CONSTRAINT ck_laboral_otros_ingresos CHECK (otros_ingresos >= 0)
);

CREATE TABLE cotizante (
    id_cotizante BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    numero_identificacion_aportante VARCHAR(60),
    razon_social_aportante VARCHAR(200) NOT NULL,
    valor_ingreso NUMERIC(18,2),
    promedio_ultimos_3_meses NUMERIC(18,2),
    mediana NUMERIC(18,2),
    moda NUMERIC(18,2),
    tendencia VARCHAR(40),
    percentil NUMERIC(8,4),
    meses_continuidad INTEGER,
    CONSTRAINT uq_cotizante_solicitud_aportante UNIQUE (id_solicitud, razon_social_aportante),
    CONSTRAINT ck_cotizante_ingreso CHECK (valor_ingreso IS NULL OR valor_ingreso >= 0)
);

CREATE OR REPLACE FUNCTION validar_maximo_cotizantes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    PERFORM pg_advisory_xact_lock(hashtextextended(NEW.id_solicitud::TEXT, 0));
    IF (SELECT COUNT(*) FROM cotizante WHERE id_solicitud = NEW.id_solicitud) >= 5 THEN
        RAISE EXCEPTION 'Una solicitud no puede tener mas de 5 cotizantes';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_cotizante_maximo
BEFORE INSERT ON cotizante
FOR EACH ROW
EXECUTE FUNCTION validar_maximo_cotizantes();

CREATE TABLE cotizante_ingreso_mensual (
    id_cotizante BIGINT NOT NULL REFERENCES cotizante(id_cotizante) ON DELETE CASCADE,
    periodo DATE NOT NULL,
    ingreso NUMERIC(18,2) NOT NULL,
    PRIMARY KEY (id_cotizante, periodo),
    CONSTRAINT ck_cotizante_ingreso_mensual CHECK (ingreso >= 0)
);

CREATE TABLE evaluacion_credito (
    id_evaluacion BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    version SMALLINT NOT NULL DEFAULT 1,
    vigente BOOLEAN NOT NULL DEFAULT TRUE,
    id_usuario_evaluador UUID REFERENCES usuario(id_usuario) ON DELETE SET NULL,
    fecha_evaluacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    origen_evaluacion VARCHAR(40) NOT NULL DEFAULT 'motor_pacifico',
    quanto NUMERIC(18,2),
    quanto_3_medio NUMERIC(18,2),
    valor_ingreso NUMERIC(18,2),
    ingreso_final NUMERIC(18,2),
    score NUMERIC(8,2),
    obligaciones_reestructuradas INTEGER NOT NULL DEFAULT 0,
    calificacion_diferente_ab INTEGER NOT NULL DEFAULT 0,
    mora_historica_90 INTEGER NOT NULL DEFAULT 0,
    mora_historica_60 INTEGER NOT NULL DEFAULT 0,
    mora_historica_30 INTEGER NOT NULL DEFAULT 0,
    mora_60 INTEGER NOT NULL DEFAULT 0,
    mora_30 INTEGER NOT NULL DEFAULT 0,
    gastos_rotativos NUMERIC(18,2) NOT NULL DEFAULT 0,
    gastos_no_rotativos NUMERIC(18,2) NOT NULL DEFAULT 0,
    endeudamiento NUMERIC(8,4),
    embargo INTEGER NOT NULL DEFAULT 0,
    dudoso_recaudo INTEGER NOT NULL DEFAULT 0,
    documento_vigente BOOLEAN,
    disponible NUMERIC(18,2),
    cartera_castigada INTEGER NOT NULL DEFAULT 0,
    capacidad_pago NUMERIC(18,2),
    cancelaciones_negativas INTEGER NOT NULL DEFAULT 0,
    edad SMALLINT,
    ingresos NUMERIC(18,2),
    meses_continuidad INTEGER,
    meses_antiguedad INTEGER,
    CONSTRAINT uq_evaluacion_version UNIQUE (id_solicitud, version),
    CONSTRAINT ck_evaluacion_version CHECK (version > 0),
    CONSTRAINT ck_evaluacion_conteos CHECK (
        obligaciones_reestructuradas >= 0 AND calificacion_diferente_ab >= 0
        AND mora_historica_90 >= 0 AND mora_historica_60 >= 0
        AND mora_historica_30 >= 0 AND mora_60 >= 0 AND mora_30 >= 0
        AND embargo >= 0 AND dudoso_recaudo >= 0 AND cartera_castigada >= 0
        AND cancelaciones_negativas >= 0
    )
);

CREATE UNIQUE INDEX uq_evaluacion_vigente
ON evaluacion_credito (id_solicitud)
WHERE vigente = TRUE;

CREATE TABLE criterio_evaluacion (
    id_criterio SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(60) NOT NULL UNIQUE,
    descripcion VARCHAR(200),
    tipo tipo_criterio NOT NULL
);

CREATE TABLE evaluacion_detalle (
    id_evaluacion_detalle BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_evaluacion BIGINT NOT NULL REFERENCES evaluacion_credito(id_evaluacion) ON DELETE CASCADE,
    id_criterio SMALLINT NOT NULL REFERENCES criterio_evaluacion(id_criterio),
    resultado BOOLEAN NOT NULL,
    puntaje NUMERIC(8,2),
    causal TEXT,
    CONSTRAINT uq_evaluacion_criterio UNIQUE (id_evaluacion, id_criterio)
);

CREATE TABLE solicitud_causal (
    id_solicitud_causal BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    id_criterio SMALLINT REFERENCES criterio_evaluacion(id_criterio),
    codigo VARCHAR(60) NOT NULL,
    descripcion TEXT NOT NULL,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_registro TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_solicitud_causal UNIQUE (id_solicitud, codigo)
);

CREATE TABLE capacidad_pago (
    id_capacidad BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    version SMALLINT NOT NULL DEFAULT 1,
    vigente BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_calculo TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_capacidad_version UNIQUE (id_solicitud, version),
    CONSTRAINT ck_capacidad_version CHECK (version > 0),
    salario_minimo NUMERIC(18,2),
    ingreso_final NUMERIC(18,2),
    ingreso_final_smlmv NUMERIC(8,4),
    gastos_personales NUMERIC(18,2),
    disponible_1 NUMERIC(18,2),
    capacidad_pago_2 NUMERIC(18,2),
    tasa_cupo NUMERIC(8,4),
    plazo_cupo INTEGER,
    cupo_calculado NUMERIC(18,2),
    cupo_aprobado NUMERIC(18,2)
);

CREATE UNIQUE INDEX uq_capacidad_vigente
ON capacidad_pago (id_solicitud)
WHERE vigente = TRUE;

CREATE OR REPLACE FUNCTION desmarcar_versiones_previas()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF NOT NEW.vigente OR (TG_OP = 'UPDATE' AND NEW.vigente = OLD.vigente) THEN
        RETURN NEW;
    END IF;
    IF NEW.vigente THEN
        IF TG_TABLE_NAME = 'evaluacion_credito' THEN
            UPDATE evaluacion_credito
            SET vigente = FALSE
            WHERE id_solicitud = NEW.id_solicitud
              AND id_evaluacion IS DISTINCT FROM NEW.id_evaluacion
              AND vigente = TRUE;
        ELSE
            UPDATE capacidad_pago
            SET vigente = FALSE
            WHERE id_solicitud = NEW.id_solicitud
              AND id_capacidad IS DISTINCT FROM NEW.id_capacidad
              AND vigente = TRUE;
        END IF;
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_evaluacion_vigente
BEFORE INSERT OR UPDATE ON evaluacion_credito
FOR EACH ROW
EXECUTE FUNCTION desmarcar_versiones_previas();

CREATE TRIGGER trg_capacidad_vigente
BEFORE INSERT OR UPDATE ON capacidad_pago
FOR EACH ROW
EXECUTE FUNCTION desmarcar_versiones_previas();

CREATE TABLE producto_vehiculo (
    id_vehiculo BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    producto_a_financiar VARCHAR(180) NOT NULL,
    marca VARCHAR(100),
    referencia VARCHAR(120),
    modelo VARCHAR(30),
    color VARCHAR(60),
    valor_moto_iva NUMERIC(18,2),
    descuento_pesos NUMERIC(18,2) NOT NULL DEFAULT 0,
    descuento_pct NUMERIC(8,4) NOT NULL DEFAULT 0,
    accesorios NUMERIC(18,2) NOT NULL DEFAULT 0,
    matricula NUMERIC(18,2) NOT NULL DEFAULT 0,
    soat NUMERIC(18,2) NOT NULL DEFAULT 0,
    impuestos NUMERIC(18,2) NOT NULL DEFAULT 0,
    CONSTRAINT ck_vehiculo_descuento_pct CHECK (descuento_pct BETWEEN 0 AND 100)
);

CREATE TABLE credito_financiacion (
    id_credito BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    id_vehiculo BIGINT NOT NULL REFERENCES producto_vehiculo(id_vehiculo),
    id_oferta BIGINT REFERENCES oferta_credito(id_oferta),
    id_aliado_financiero BIGINT REFERENCES aliado_financiero(id_aliado),
    ganadora BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    aval_pct NUMERIC(8,4),
    tasa NUMERIC(8,4) NOT NULL,
    plazo INTEGER NOT NULL,
    seguro NUMERIC(18,2) NOT NULL DEFAULT 0,
    cuota_inicial NUMERIC(18,2) NOT NULL DEFAULT 0,
    valor_financiar NUMERIC(18,2) NOT NULL,
    gastos_administrativos NUMERIC(18,2) NOT NULL DEFAULT 0,
    saldo_financiar NUMERIC(18,2) NOT NULL,
    valor_financiacion NUMERIC(18,2) NOT NULL,
    valor_seguro_vida NUMERIC(18,2) NOT NULL DEFAULT 0,
    total_a_pagar NUMERIC(18,2) NOT NULL,
    cuota_financiacion NUMERIC(18,2) NOT NULL,
    cuota_seguro_vida NUMERIC(18,2) NOT NULL DEFAULT 0,
    cuota_total NUMERIC(18,2) NOT NULL,
    moneda CHAR(3) NOT NULL DEFAULT 'COP',
    dia_pago SMALLINT,
    fecha_inicio DATE,
    fecha_fin DATE,
    CONSTRAINT ck_credito_plazo CHECK (plazo > 0),
    CONSTRAINT ck_credito_dia_pago CHECK (dia_pago IS NULL OR dia_pago BETWEEN 1 AND 31),
    CONSTRAINT ck_credito_moneda CHECK (moneda ~ '^[A-Z]{3}$'),
    CONSTRAINT ck_credito_origen CHECK (
        (id_oferta IS NULL AND id_aliado_financiero IS NULL)
        OR (id_oferta IS NOT NULL AND id_aliado_financiero IS NOT NULL)
    )
);

CREATE UNIQUE INDEX uq_financiacion_oferta
ON credito_financiacion (id_oferta)
WHERE id_oferta IS NOT NULL;

CREATE UNIQUE INDEX uq_financiacion_ganadora
ON credito_financiacion (id_solicitud)
WHERE ganadora = TRUE;

CREATE TABLE aseguradora (
    id_aseguradora BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nit VARCHAR(30) NOT NULL UNIQUE,
    nombre VARCHAR(180) NOT NULL UNIQUE,
    telefono VARCHAR(40),
    correo CITEXT,
    activa BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE banco (
    id_banco BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_ach VARCHAR(10) UNIQUE,
    nombre VARCHAR(180) NOT NULL UNIQUE,
    nit VARCHAR(30) UNIQUE,
    pais VARCHAR(80) NOT NULL DEFAULT 'Colombia',
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_banco_codigo_ach CHECK (codigo_ach IS NULL OR codigo_ach ~ '^[0-9]{1,10}$')
);

CREATE TABLE cuenta_bancaria (
    id_cuenta BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_banco BIGINT NOT NULL REFERENCES banco(id_banco),
    tipo tipo_cuenta NOT NULL,
    numero VARCHAR(40) NOT NULL,
    titular VARCHAR(180) NOT NULL,
    nit_titular VARCHAR(30),
    id_aliado BIGINT REFERENCES aliado_financiero(id_aliado) ON DELETE CASCADE,
    id_concesionario BIGINT REFERENCES concesionario(id_concesionario) ON DELETE CASCADE,
    id_cliente BIGINT REFERENCES cliente(id_cliente) ON DELETE CASCADE,
    activa BOOLEAN NOT NULL DEFAULT TRUE,
    fecha_creacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_cuenta_un_solo_titular CHECK (
        (id_aliado IS NOT NULL)::INT
        + (id_concesionario IS NOT NULL)::INT
        + (id_cliente IS NOT NULL)::INT = 1
    ),
    CONSTRAINT ck_cuenta_cliente_solo_ahorros CHECK (
        id_cliente IS NULL OR tipo = 'ahorros'
    ),
    CONSTRAINT uq_cuenta_banco_numero_tipo UNIQUE (id_banco, numero, tipo)
);

CREATE INDEX ix_cuenta_aliado ON cuenta_bancaria (id_aliado) WHERE id_aliado IS NOT NULL;
CREATE INDEX ix_cuenta_concesionario ON cuenta_bancaria (id_concesionario) WHERE id_concesionario IS NOT NULL;
CREATE INDEX ix_cuenta_cliente ON cuenta_bancaria (id_cliente) WHERE id_cliente IS NOT NULL;

CREATE TABLE seguro_producto (
    id_seguro_producto BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_aseguradora BIGINT NOT NULL REFERENCES aseguradora(id_aseguradora),
    tipo tipo_seguro NOT NULL,
    nombre VARCHAR(180) NOT NULL,
    descripcion TEXT,
    vigencia_meses SMALLINT NOT NULL DEFAULT 12,
    valor_asegurado_min NUMERIC(18,2),
    valor_asegurado_max NUMERIC(18,2),
    tasa_prima NUMERIC(10,6),
    prima_minima NUMERIC(18,2),
    deducible_pct NUMERIC(8,4),
    comision_pct NUMERIC(8,4),
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT uq_seguro_producto UNIQUE (id_aseguradora, tipo, nombre),
    CONSTRAINT ck_seguro_vigencia CHECK (vigencia_meses > 0),
    CONSTRAINT ck_seguro_valor_asegurado CHECK (
        valor_asegurado_min IS NULL OR valor_asegurado_max IS NULL
        OR valor_asegurado_max >= valor_asegurado_min
    ),
    CONSTRAINT ck_seguro_porcentajes CHECK (
        (deducible_pct IS NULL OR deducible_pct BETWEEN 0 AND 100)
        AND (comision_pct IS NULL OR comision_pct BETWEEN 0 AND 100)
        AND (tasa_prima IS NULL OR tasa_prima BETWEEN 0 AND 100)
    )
);

CREATE TABLE seguro_cotizacion (
    id_cotizacion BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    id_seguro_producto BIGINT NOT NULL REFERENCES seguro_producto(id_seguro_producto),
    tipo tipo_seguro NOT NULL,
    valor_asegurado NUMERIC(18,2) NOT NULL,
    prima_total NUMERIC(18,2) NOT NULL,
    prima_mensual NUMERIC(18,2),
    comision_valor NUMERIC(18,2),
    moneda CHAR(3) NOT NULL DEFAULT 'COP',
    seleccionada BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_cotizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_seguro_cotizacion_moneda CHECK (moneda ~ '^[A-Z]{3}$')
);

CREATE UNIQUE INDEX uq_seguro_cotizacion_seleccionada
ON seguro_cotizacion (id_solicitud, tipo)
WHERE seleccionada = TRUE;

CREATE TABLE poliza (
    id_poliza BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    numero_poliza VARCHAR(60) UNIQUE,
    id_cotizacion BIGINT REFERENCES seguro_cotizacion(id_cotizacion),
    id_solicitud UUID NOT NULL REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    id_credito BIGINT REFERENCES credito_financiacion(id_credito),
    id_seguro_producto BIGINT NOT NULL REFERENCES seguro_producto(id_seguro_producto),
    tipo tipo_seguro NOT NULL,
    valor_asegurado NUMERIC(18,2) NOT NULL,
    prima_total NUMERIC(18,2) NOT NULL,
    prima_mensual NUMERIC(18,2),
    comision_valor NUMERIC(18,2),
    moneda CHAR(3) NOT NULL DEFAULT 'COP',
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    estado estado_poliza NOT NULL DEFAULT 'emitida',
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_poliza_fechas CHECK (fecha_fin > fecha_inicio),
    CONSTRAINT ck_poliza_moneda CHECK (moneda ~ '^[A-Z]{3}$')
);

CREATE INDEX ix_poliza_solicitud ON poliza (id_solicitud);
CREATE INDEX ix_poliza_vigencia ON poliza (fecha_fin) WHERE estado = 'vigente';

CREATE OR REPLACE FUNCTION sincronizar_tipo_seguro()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    SELECT tipo INTO NEW.tipo
    FROM seguro_producto
    WHERE id_seguro_producto = NEW.id_seguro_producto;
    IF NEW.tipo IS NULL THEN
        RAISE EXCEPTION 'El producto de seguro no existe';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_cotizacion_tipo_seguro
BEFORE INSERT OR UPDATE OF id_seguro_producto ON seguro_cotizacion
FOR EACH ROW EXECUTE FUNCTION sincronizar_tipo_seguro();

CREATE TRIGGER trg_poliza_tipo_seguro
BEFORE INSERT OR UPDATE OF id_seguro_producto ON poliza
FOR EACH ROW EXECUTE FUNCTION sincronizar_tipo_seguro();

CREATE TABLE desembolso (
    id_desembolso BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    num_desembolso VARCHAR(30) UNIQUE,

    -- Crédito asociado
    id_credito BIGINT NOT NULL REFERENCES credito_financiacion(id_credito),

    -- Quién envía el dinero (emisor)
    id_cuenta_emisor BIGINT NOT NULL REFERENCES cuenta_bancaria(id_cuenta),
    emisor VARCHAR(180) NOT NULL,

    -- Quién recibe el dinero (receptor)
    id_cuenta_receptor BIGINT NOT NULL REFERENCES cuenta_bancaria(id_cuenta),
    nit_receptor VARCHAR(30),
    receptor VARCHAR(180) NOT NULL,

    referencia_pago VARCHAR(80),

    -- Cuándo
    fecha_desembolso TIMESTAMPTZ,
    fecha_anexo TIMESTAMPTZ,
    capital NUMERIC(18,2) NOT NULL,
    cuota NUMERIC(18,2) NOT NULL,
    plazo INTEGER NOT NULL,
    tasa NUMERIC(8,4) NOT NULL,
    valor_seguro NUMERIC(18,2) NOT NULL DEFAULT 0,
    moneda CHAR(3) NOT NULL DEFAULT 'COP',
    estado estado_desembolso NOT NULL DEFAULT 'pendiente',
    fecha_actualizacion TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT ck_desembolso_moneda CHECK (moneda ~ '^[A-Z]{3}$'),
    CONSTRAINT ck_desembolso_plazo CHECK (plazo > 0),
    CONSTRAINT ck_desembolso_montos CHECK (capital >= 0 AND cuota >= 0 AND valor_seguro >= 0),
    CONSTRAINT ck_desembolso_cuentas_distintas CHECK (
        id_cuenta_emisor <> id_cuenta_receptor
    )
);

COMMENT ON COLUMN desembolso.emisor IS
    'Snapshot al momento del desembolso; la fuente viva es cuenta_bancaria.titular';
COMMENT ON COLUMN desembolso.receptor IS
    'Snapshot al momento del desembolso; la fuente viva es cuenta_bancaria.titular';
COMMENT ON COLUMN desembolso.id_cuenta_emisor IS
    'Cuenta bancaria del aliado propio que envía el dinero';
COMMENT ON COLUMN desembolso.id_cuenta_receptor IS
    'Cuenta de ahorros activa del cliente que recibe el desembolso';
COMMENT ON COLUMN desembolso.referencia_pago IS
    'Número de transacción o referencia de la transferencia bancaria';

CREATE INDEX ix_desembolso_credito_estado ON desembolso (id_credito, estado);
CREATE INDEX ix_desembolso_referencia ON desembolso (referencia_pago) WHERE referencia_pago IS NOT NULL;

CREATE OR REPLACE FUNCTION validar_cuentas_desembolso()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    v_id_cliente BIGINT;
BEGIN
    SELECT sc.id_cliente INTO v_id_cliente
    FROM credito_financiacion cf
    JOIN solicitud_credito sc ON sc.id_solicitud = cf.id_solicitud
    WHERE cf.id_credito = NEW.id_credito;

    IF v_id_cliente IS NULL THEN
        RAISE EXCEPTION 'No se pudo determinar el cliente del crédito %', NEW.id_credito;
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM cuenta_bancaria cb
        JOIN aliado_financiero af ON af.id_aliado = cb.id_aliado
        WHERE cb.id_cuenta = NEW.id_cuenta_emisor
            AND cb.activa = TRUE
            AND af.es_propio = TRUE
            AND af.activo = TRUE
    ) THEN
        RAISE EXCEPTION 'La cuenta emisora debe estar activa y pertenecer a un aliado propio';
    END IF;

    IF NOT EXISTS (
        SELECT 1
        FROM cuenta_bancaria
        WHERE id_cuenta = NEW.id_cuenta_receptor
            AND id_cliente = v_id_cliente
            AND tipo = 'ahorros'
            AND activa = TRUE
    ) THEN
        RAISE EXCEPTION 'La cuenta receptora debe ser una cuenta de ahorros activa del cliente';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_desembolso_cuentas
BEFORE INSERT OR UPDATE OF id_cuenta_emisor, id_cuenta_receptor, id_credito ON desembolso
FOR EACH ROW EXECUTE FUNCTION validar_cuentas_desembolso();

CREATE TABLE otp (
    id_otp BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    codigo_otp_hash TEXT NOT NULL,
    fecha_hora_otp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_expiracion TIMESTAMPTZ NOT NULL,
    otp_aprobacion TIMESTAMPTZ,
    fecha_hora_otp_aprobacion TIMESTAMPTZ,
    intentos_fallidos SMALLINT NOT NULL DEFAULT 0,
    ip_solicitud INET,
    autenticacion VARCHAR(100),
    accion VARCHAR(100),
    estado estado_otp NOT NULL DEFAULT 'pendiente',
    CONSTRAINT ck_otp_intentos CHECK (intentos_fallidos >= 0)
);

CREATE TABLE metricas_reporte (
    id_metrica BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_solicitud UUID NOT NULL REFERENCES solicitud_credito(id_solicitud) ON DELETE CASCADE,
    id_aliado_financiero BIGINT REFERENCES aliado_financiero(id_aliado),
    indice VARCHAR(100) NOT NULL,
    aprobados INTEGER NOT NULL DEFAULT 0,
    saldo_aprobados NUMERIC(18,2) NOT NULL DEFAULT 0,
    comision NUMERIC(18,2) NOT NULL DEFAULT 0,
    comision_mostrar NUMERIC(18,2) NOT NULL DEFAULT 0,
    CONSTRAINT uq_metrica_solicitud_indice
        UNIQUE (id_solicitud, indice, id_aliado_financiero)
);

CREATE TABLE auditoria_usuario (
    id_auditoria BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_usuario UUID REFERENCES usuario(id_usuario) ON DELETE SET NULL,
    accion VARCHAR(100) NOT NULL,
    descripcion TEXT,
    ip INET,
    fecha_hora TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE auditoria_cambio (
    id_cambio BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tabla VARCHAR(80) NOT NULL,
    id_registro TEXT NOT NULL,
    campo VARCHAR(120) NOT NULL,
    valor_anterior TEXT,
    valor_nuevo TEXT,
    id_usuario UUID REFERENCES usuario(id_usuario) ON DELETE SET NULL,
    fecha_hora TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION auditar_cambio_fila()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
DECLARE
    datos_nuevos JSONB;
    datos_anteriores JSONB;
    campo_actual TEXT;
    usuario_actual UUID;
    id_actual TEXT;
BEGIN
    datos_nuevos = CASE WHEN TG_OP = 'DELETE' THEN NULL ELSE to_jsonb(NEW) END;
    datos_anteriores = CASE WHEN TG_OP = 'INSERT' THEN NULL ELSE to_jsonb(OLD) END;
    usuario_actual = CASE
        WHEN current_setting('app.user_id', TRUE) ~ '^[0-9a-fA-F-]{36}$'
        THEN current_setting('app.user_id', TRUE)::UUID
        ELSE NULL
    END;
    id_actual = COALESCE(
        datos_nuevos->>'id_solicitud', datos_anteriores->>'id_solicitud',
        datos_nuevos->>'id_credito', datos_anteriores->>'id_credito',
        datos_nuevos->>'id_oferta', datos_anteriores->>'id_oferta',
        datos_nuevos->>'id_poliza', datos_anteriores->>'id_poliza',
        datos_nuevos->>'id_desembolso', datos_anteriores->>'id_desembolso',
        datos_nuevos->>'id_aliado_producto', datos_anteriores->>'id_aliado_producto',
        datos_nuevos->>'id_aliado', datos_anteriores->>'id_aliado',
        datos_nuevos->>'id_cuenta', datos_anteriores->>'id_cuenta',
        datos_nuevos->>'id_banco', datos_anteriores->>'id_banco'
    );

    FOR campo_actual IN
        SELECT COALESCE(n.key, o.key)
        FROM jsonb_each_text(COALESCE(datos_nuevos, '{}'::JSONB)) n
        FULL OUTER JOIN jsonb_each_text(COALESCE(datos_anteriores, '{}'::JSONB)) o ON o.key = n.key
                WHERE (TG_OP <> 'UPDATE' OR n.value IS DISTINCT FROM o.value)
                    AND COALESCE(n.key, o.key) NOT IN ('fecha_actualizacion', 'fecha_creacion')
    LOOP
        INSERT INTO auditoria_cambio (
            tabla, id_registro, campo, valor_anterior, valor_nuevo, id_usuario
        )
        VALUES (
            TG_TABLE_NAME,
            COALESCE(id_actual, 'desconocido'),
            campo_actual,
            datos_anteriores->>campo_actual,
            datos_nuevos->>campo_actual,
            usuario_actual
        );
    END LOOP;
    IF TG_OP = 'DELETE' THEN
        RETURN OLD;
    END IF;
    RETURN NEW;
END;
$$;

CREATE INDEX ix_auditoria_cambio_tabla ON auditoria_cambio (tabla, id_registro, fecha_hora);

CREATE TRIGGER trg_solicitud_actualizacion
BEFORE UPDATE ON solicitud_credito
FOR EACH ROW EXECUTE FUNCTION actualizar_fecha_actualizacion();

CREATE TRIGGER trg_aliado_producto_actualizacion
BEFORE UPDATE ON aliado_producto
FOR EACH ROW EXECUTE FUNCTION actualizar_fecha_actualizacion();

CREATE TRIGGER trg_aliado_financiero_actualizacion
BEFORE UPDATE ON aliado_financiero
FOR EACH ROW EXECUTE FUNCTION actualizar_fecha_actualizacion();

CREATE TRIGGER trg_oferta_actualizacion
BEFORE UPDATE ON oferta_credito
FOR EACH ROW EXECUTE FUNCTION actualizar_fecha_actualizacion();

CREATE TRIGGER trg_credito_actualizacion
BEFORE UPDATE ON credito_financiacion
FOR EACH ROW EXECUTE FUNCTION actualizar_fecha_actualizacion();

CREATE TRIGGER trg_seguro_producto_actualizacion
BEFORE UPDATE ON seguro_producto
FOR EACH ROW EXECUTE FUNCTION actualizar_fecha_actualizacion();

CREATE TRIGGER trg_poliza_actualizacion
BEFORE UPDATE ON poliza
FOR EACH ROW EXECUTE FUNCTION actualizar_fecha_actualizacion();

CREATE TRIGGER trg_desembolso_actualizacion
BEFORE UPDATE ON desembolso
FOR EACH ROW EXECUTE FUNCTION actualizar_fecha_actualizacion();

CREATE TRIGGER trg_cuenta_bancaria_actualizacion
BEFORE UPDATE ON cuenta_bancaria
FOR EACH ROW EXECUTE FUNCTION actualizar_fecha_actualizacion();

CREATE TRIGGER trg_banco_actualizacion
BEFORE UPDATE ON banco
FOR EACH ROW EXECUTE FUNCTION actualizar_fecha_actualizacion();

CREATE TRIGGER trg_auditoria_solicitud
AFTER INSERT OR UPDATE OR DELETE ON solicitud_credito
FOR EACH ROW EXECUTE FUNCTION auditar_cambio_fila();

CREATE TRIGGER trg_auditoria_oferta
AFTER INSERT OR UPDATE OR DELETE ON oferta_credito
FOR EACH ROW EXECUTE FUNCTION auditar_cambio_fila();

CREATE TRIGGER trg_auditoria_credito
AFTER INSERT OR UPDATE OR DELETE ON credito_financiacion
FOR EACH ROW EXECUTE FUNCTION auditar_cambio_fila();

CREATE TRIGGER trg_auditoria_poliza
AFTER INSERT OR UPDATE OR DELETE ON poliza
FOR EACH ROW EXECUTE FUNCTION auditar_cambio_fila();

CREATE TRIGGER trg_auditoria_desembolso
AFTER INSERT OR UPDATE OR DELETE ON desembolso
FOR EACH ROW EXECUTE FUNCTION auditar_cambio_fila();

CREATE TRIGGER trg_auditoria_cuenta_bancaria
AFTER INSERT OR UPDATE OR DELETE ON cuenta_bancaria
FOR EACH ROW EXECUTE FUNCTION auditar_cambio_fila();

CREATE TRIGGER trg_auditoria_banco
AFTER INSERT OR UPDATE OR DELETE ON banco
FOR EACH ROW EXECUTE FUNCTION auditar_cambio_fila();

CREATE TRIGGER trg_auditoria_aliado_producto
AFTER INSERT OR UPDATE OR DELETE ON aliado_producto
FOR EACH ROW EXECUTE FUNCTION auditar_cambio_fila();

CREATE OR REPLACE FUNCTION impedir_eliminacion_usuario()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    RAISE EXCEPTION 'Los usuarios no se eliminan fisicamente; deben marcarse como inactivos';
END;
$$;

CREATE TRIGGER trg_usuario_fecha_actualizacion
BEFORE UPDATE ON usuario
FOR EACH ROW
EXECUTE FUNCTION actualizar_fecha_actualizacion();

CREATE TRIGGER trg_usuario_no_delete
BEFORE DELETE ON usuario
FOR EACH ROW
EXECUTE FUNCTION impedir_eliminacion_usuario();

CREATE INDEX ix_solicitud_cliente ON solicitud_credito (id_cliente);
CREATE INDEX ix_solicitud_estado ON solicitud_credito (estado);
CREATE INDEX ix_solicitud_fecha_hora ON solicitud_credito (fecha_hora);
CREATE INDEX ix_solicitud_asesor_estado ON solicitud_credito (id_asesor, estado);
CREATE INDEX ix_solicitud_concesionario_fecha ON solicitud_credito (id_concesionario, fecha_hora);
CREATE INDEX ix_solicitud_estado_historial ON solicitud_estado_historial (id_solicitud, fecha_hora);
CREATE INDEX ix_solicitud_causal_solicitud ON solicitud_causal (id_solicitud) WHERE activa = TRUE;
CREATE INDEX ix_cotizante_solicitud ON cotizante (id_solicitud);
CREATE INDEX ix_evaluacion_detalle_eval_resultado ON evaluacion_detalle (id_evaluacion, resultado);
CREATE INDEX ix_otp_solicitud_estado ON otp (id_solicitud, estado);
CREATE INDEX ix_oferta_aliado_fecha ON oferta_credito (id_aliado_producto, fecha_generacion);
CREATE INDEX ix_seguro_cotizacion_solicitud ON seguro_cotizacion (id_solicitud, fecha_cotizacion);
CREATE INDEX ix_poliza_credito ON poliza (id_credito) WHERE id_credito IS NOT NULL;
CREATE INDEX ix_auditoria_usuario_fecha ON auditoria_usuario (id_usuario, fecha_hora);