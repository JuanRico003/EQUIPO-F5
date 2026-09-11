class RegistroBeneficiario:
    """
    Representa un registro individual de beneficiario del programa agrícola,
    con los datos ya limpios y convertidos al tipo correcto.
    """

    def __init__(self, consecutivo, fecha_actualizacion, vigencia_presupuestal,
                 tipo_documento, sexo, etnia, discapacidad, departamento,
                 municipio, codigo_municipio, vereda, linea_productiva, hectareas):
        self.consecutivo = consecutivo
        self.fecha_actualizacion = fecha_actualizacion
        self.vigencia_presupuestal = vigencia_presupuestal
        self.tipo_documento = tipo_documento
        self.sexo = sexo
        self.etnia = etnia
        self.discapacidad = discapacidad
        self.departamento = departamento
        self.municipio = municipio
        self.codigo_municipio = codigo_municipio
        self.vereda = vereda
        self.linea_productiva = linea_productiva
        self.hectareas = hectareas

    def __repr__(self):
        return (f"RegistroBeneficiario(consecutivo={self.consecutivo}, "
                f"vereda='{self.vereda}', linea_productiva='{self.linea_productiva}', "
                f"hectareas={self.hectareas})")

    @staticmethod
    def _a_entero_seguro(valor, por_defecto=0):
        """Convierte a int de forma segura"""
        try:
            return int(valor)
        except (ValueError, TypeError):
            return por_defecto

    @staticmethod
    def _a_float_seguro(valor, por_defecto=0.0):
        """Convierte a float de forma segura"""
        try:
            return float(valor)
        except (ValueError, TypeError):
            return por_defecto

    @classmethod
    def desde_json(cls, datos_json):
        return cls(
            consecutivo=cls._a_entero_seguro(datos_json.get("consecutivo")),
            fecha_actualizacion=datos_json.get("fecha_de_actualizaci_n") or "",
            vigencia_presupuestal=cls._a_entero_seguro(datos_json.get("vigencia_presupuestal")),
            tipo_documento=datos_json.get("tipo_de_documento") or "",
            sexo=datos_json.get("sexo") or "",
            etnia=datos_json.get("etnia") or "",
            discapacidad=datos_json.get("discapacidad") or "",
            departamento=datos_json.get("departamento") or "",
            municipio=datos_json.get("municipio") or "",
            codigo_municipio=cls._a_entero_seguro(datos_json.get("codigo_de_municipio")),
            vereda=datos_json.get("vereda") or "",
            linea_productiva=datos_json.get("liena_productiva") or "",
            hectareas=cls._a_float_seguro(datos_json.get("hectareas")),
        )