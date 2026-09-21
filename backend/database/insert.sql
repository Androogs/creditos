INSERT INTO rol (nombre, descripcion) VALUES
    ('cliente', 'Usuario solicitante'),
    ('asesor', 'Asesor comercial'),
    ('aliado', 'Usuario de aliado comercial'),
    ('admin', 'Administrador de la plataforma'),
    ('contabilidad', 'Usuario de contabilidad')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO aliado_financiero (nit, nombre, tipo, sitio_web)
VALUES ('814005081', 'INVERSIONES PACIFICO S.A.', 'otro', NULL)
ON CONFLICT (nit) DO NOTHING;

UPDATE aliado_financiero
SET es_propio = TRUE
WHERE nit = '814005081';

INSERT INTO concesionario (nombre) VALUES
    ('TULUA MOTOS SA'),
    ('SUMOTO SA PALMIRA'),
    ('PIJAOS MOTOS S.A')
ON CONFLICT (nombre) DO NOTHING;

INSERT INTO aliado_concesionario (id_aliado, id_concesionario)
SELECT a.id_aliado, c.id_concesionario
FROM aliado_financiero a
CROSS JOIN concesionario c
WHERE a.nit = '814005081'
    AND c.nombre IN ('TULUA MOTOS SA', 'SUMOTO SA PALMIRA', 'PIJAOS MOTOS S.A')
ON CONFLICT (id_aliado, id_concesionario) DO NOTHING;

INSERT INTO banco (codigo_ach, nombre, nit) VALUES
    ('007', 'BANCOLOMBIA', '890903938'),
    ('009', 'BANCO DE BOGOTA', '860002964'),
    ('012', 'BBVA COLOMBIA', '860003020'),
    ('013', 'BANCO DAVIVIENDA', '860034313'),
    ('023', 'BANCO DE OCCIDENTE', '890300279'),
    ('051', 'BANCO AV VILLAS', '860007336'),
    ('052', 'BANCO CAJA SOCIAL', '860007338'),
    ('100', 'BANCO W', '900091362'),
    ('102', 'BANCO UNION', '890200486')
ON CONFLICT (codigo_ach) DO NOTHING;

INSERT INTO cuenta_bancaria (id_banco, tipo, numero, titular, nit_titular, id_aliado)
SELECT b.id_banco, 'ahorros', '0000000000', 'INVERSIONES PACIFICO S.A.',
       '814005081', a.id_aliado
FROM banco b, aliado_financiero a
WHERE b.codigo_ach = '007'
    AND a.nit = '814005081'
ON CONFLICT (id_banco, numero, tipo) DO NOTHING;

INSERT INTO cuenta_bancaria (id_banco, tipo, numero, titular, id_concesionario)
-- TODO: reemplazar los números de cuenta ficticios por cuentas reales antes de producción.
SELECT b.id_banco, 'ahorros', c.nombre || '-CTA', c.nombre, c.id_concesionario
FROM banco b, concesionario c
WHERE b.codigo_ach = '007'
    AND c.nombre IN ('TULUA MOTOS SA', 'SUMOTO SA PALMIRA', 'PIJAOS MOTOS S.A')
ON CONFLICT (id_banco, numero, tipo) DO NOTHING;

INSERT INTO aliado_producto (id_aliado, nombre)
SELECT id_aliado, 'Financiacion de motocicleta'
FROM aliado_financiero
WHERE nit = '814005081'
ON CONFLICT (id_aliado, nombre) DO NOTHING;

INSERT INTO criterio_evaluacion (codigo, descripcion, tipo) VALUES
    ('EDAD_POLITICA', 'Edad entre 18 y 65 anos', 'interno'),
    ('NACIONALIDAD_COLOMBIANA', 'Nacionalidad colombiana', 'interno'),
    ('DOCUMENTO_VIGENTE', 'Documento de identidad vigente', 'buro'),
    ('EMBARGOS_VIGENTES', 'Embargos vigentes', 'buro'),
    ('CARTERA_CASTIGADA', 'Cartera castigada vigente en los ultimos 12 meses', 'buro'),
    ('DUDOSO_RECAUDO', 'Obligaciones de dudoso recaudo', 'buro'),
    ('MORA_30_VIGENTE', 'Mora vigente de 30 dias o mas', 'buro'),
    ('MORA_60_VIGENTE', 'Mora vigente de 60 dias o mas', 'buro'),
    ('MORA_HISTORICA_30', 'Mora historica de 30 dias', 'buro'),
    ('MORA_HISTORICA_60', 'Mora historica de 60 dias', 'buro'),
    ('MORA_HISTORICA_90', 'Mora historica de 90 dias o mas', 'buro'),
    ('CALIFICACION_NO_AB', 'Calificacion diferente de A o B', 'buro'),
    ('REESTRUCTURACION', 'Obligaciones reestructuradas', 'buro'),
    ('CANCELACION_NEGATIVA', 'Cancelacion por mal habito', 'buro'),
    ('SCORE_QUANTUM', 'Score Quantum del cliente', 'interno'),
    ('VALOR_INGRESO', 'Valor ingreso calculado', 'interno'),
    ('CAPACIDAD_PAGO', 'Capacidad de pago calculada', 'interno')
ON CONFLICT (codigo) DO NOTHING;