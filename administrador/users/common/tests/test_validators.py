"""
Tests unitarios para validadores de documentos (DNI/NIE/NIF)
"""
from django.test import TestCase
from rest_framework import serializers

from users.common.validators import (
    normalize_documento,
    validate_dni_format,
    validate_dni_nie_nif,
    validate_dni_nie_nif_serializer,
    validate_dni_serializer,
    validate_nie_format,
    validate_nie_serializer,
    validate_nif_format,
    validate_nif_serializer,
)


class DNIValidatorTestCase(TestCase):
    """Tests para validación de DNI"""

    def test_dni_valido(self):
        """Test DNI con formato y letra correcta"""
        is_valid, error = validate_dni_format("12345678Z")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_dni_valido_minusculas(self):
        """Test DNI en minúsculas (debe normalizarse)"""
        is_valid, error = validate_dni_format("12345678z")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_dni_letra_incorrecta(self):
        """Test DNI con letra incorrecta"""
        is_valid, error = validate_dni_format("12345678A")
        self.assertFalse(is_valid)
        self.assertIn("letra del DNI no es correcta", error)
        self.assertIn("Debería ser Z", error)

    def test_dni_formato_invalido_pocos_digitos(self):
        """Test DNI con menos de 8 dígitos"""
        is_valid, error = validate_dni_format("1234567A")
        self.assertFalse(is_valid)
        self.assertIn("formato del DNI no es válido", error)

    def test_dni_formato_invalido_sin_letra(self):
        """Test DNI sin letra"""
        is_valid, error = validate_dni_format("12345678")
        self.assertFalse(is_valid)
        self.assertIn("formato del DNI no es válido", error)

    def test_dni_vacio(self):
        """Test DNI vacío"""
        is_valid, error = validate_dni_format("")
        self.assertFalse(is_valid)
        self.assertIn("no puede estar vacío", error)

    def test_dni_con_espacios(self):
        """Test DNI con espacios (debe normalizarse)"""
        is_valid, error = validate_dni_format("  12345678Z  ")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")


class NIEValidatorTestCase(TestCase):
    """Tests para validación de NIE"""

    def test_nie_valido_x(self):
        """Test NIE válido comenzando con X"""
        is_valid, error = validate_nie_format("X1234567L")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_nie_valido_y(self):
        """Test NIE válido comenzando con Y"""
        is_valid, error = validate_nie_format("Y1234567X")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_nie_valido_z(self):
        """Test NIE válido comenzando con Z"""
        is_valid, error = validate_nie_format("Z1234567R")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_nie_letra_incorrecta(self):
        """Test NIE con letra final incorrecta"""
        is_valid, error = validate_nie_format("X1234567A")
        self.assertFalse(is_valid)
        self.assertIn("letra del NIE no es correcta", error)

    def test_nie_formato_invalido_letra_inicial(self):
        """Test NIE con letra inicial inválida"""
        is_valid, error = validate_nie_format("A1234567L")
        self.assertFalse(is_valid)
        self.assertIn("formato del NIE no es válido", error)

    def test_nie_vacio(self):
        """Test NIE vacío"""
        is_valid, error = validate_nie_format("")
        self.assertFalse(is_valid)
        self.assertIn("no puede estar vacío", error)


class NIFValidatorTestCase(TestCase):
    """Tests para validación de NIF"""

    def test_nif_valido(self):
        """Test NIF válido"""
        is_valid, error = validate_nif_format("B12345678")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_nif_valido_diferentes_letras(self):
        """Test NIF válido con diferentes letras iniciales válidas"""
        letras_validas = ["A", "B", "E", "H"]
        for letra in letras_validas:
            is_valid, error = validate_nif_format(f"{letra}12345678")
            self.assertTrue(is_valid, f"NIF {letra}12345678 debería ser válido")

    def test_nif_letra_invalida(self):
        """Test NIF con letra inicial inválida"""
        is_valid, error = validate_nif_format("I12345678")
        self.assertFalse(is_valid)
        self.assertIn("primera letra del NIF no es válida", error)

    def test_nif_formato_invalido(self):
        """Test NIF con formato inválido"""
        is_valid, error = validate_nif_format("12345678")
        self.assertFalse(is_valid)
        self.assertIn("formato del NIF no es válido", error)

    def test_nif_vacio(self):
        """Test NIF vacío"""
        is_valid, error = validate_nif_format("")
        self.assertFalse(is_valid)
        self.assertIn("no puede estar vacío", error)


class DNINIENIFValidatorTestCase(TestCase):
    """Tests para validación combinada DNI/NIE/NIF"""

    def test_documento_dni_valido(self):
        """Test documento tipo DNI"""
        is_valid, error = validate_dni_nie_nif("12345678Z")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_documento_nie_valido(self):
        """Test documento tipo NIE"""
        is_valid, error = validate_dni_nie_nif("X1234567L")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_documento_nif_valido(self):
        """Test documento tipo NIF"""
        is_valid, error = validate_dni_nie_nif("B12345678")
        self.assertTrue(is_valid)
        self.assertEqual(error, "")

    def test_documento_invalido(self):
        """Test documento con formato totalmente inválido"""
        is_valid, error = validate_dni_nie_nif("INVALID")
        self.assertFalse(is_valid)
        self.assertIn("Formato de documento no válido", error)

    def test_documento_vacio(self):
        """Test documento vacío"""
        is_valid, error = validate_dni_nie_nif("")
        self.assertFalse(is_valid)
        self.assertIn("no puede estar vacío", error)


class SerializerValidatorsTestCase(TestCase):
    """Tests para validadores de serializers"""

    def test_validate_dni_serializer_valido(self):
        """Test validador de DNI para serializer con DNI válido"""
        try:
            result = validate_dni_serializer("12345678Z")
            self.assertEqual(result, "12345678Z")
        except serializers.ValidationError:
            self.fail("No debería lanzar ValidationError para DNI válido")

    def test_validate_dni_serializer_invalido(self):
        """Test validador de DNI para serializer con DNI inválido"""
        with self.assertRaises(serializers.ValidationError) as context:
            validate_dni_serializer("12345678A")
        self.assertIn("letra del DNI no es correcta", str(context.exception))

    def test_validate_dni_serializer_normaliza(self):
        """Test que el validador normaliza el DNI"""
        result = validate_dni_serializer("  12345678z  ")
        self.assertEqual(result, "12345678Z")

    def test_validate_nie_serializer_valido(self):
        """Test validador de NIE para serializer con NIE válido"""
        try:
            result = validate_nie_serializer("X1234567L")
            self.assertEqual(result, "X1234567L")
        except serializers.ValidationError:
            self.fail("No debería lanzar ValidationError para NIE válido")

    def test_validate_nie_serializer_invalido(self):
        """Test validador de NIE para serializer con NIE inválido"""
        with self.assertRaises(serializers.ValidationError):
            validate_nie_serializer("X1234567A")

    def test_validate_nif_serializer_valido(self):
        """Test validador de NIF para serializer con NIF válido"""
        try:
            result = validate_nif_serializer("B12345678")
            self.assertEqual(result, "B12345678")
        except serializers.ValidationError:
            self.fail("No debería lanzar ValidationError para NIF válido")

    def test_validate_nif_serializer_invalido(self):
        """Test validador de NIF para serializer con NIF inválido"""
        with self.assertRaises(serializers.ValidationError):
            validate_nif_serializer("I12345678")

    def test_validate_dni_nie_nif_serializer_dni(self):
        """Test validador combinado con DNI"""
        result = validate_dni_nie_nif_serializer("12345678Z")
        self.assertEqual(result, "12345678Z")

    def test_validate_dni_nie_nif_serializer_nie(self):
        """Test validador combinado con NIE"""
        result = validate_dni_nie_nif_serializer("X1234567L")
        self.assertEqual(result, "X1234567L")

    def test_validate_dni_nie_nif_serializer_nif(self):
        """Test validador combinado con NIF"""
        result = validate_dni_nie_nif_serializer("B12345678")
        self.assertEqual(result, "B12345678")

    def test_validate_dni_nie_nif_serializer_invalido(self):
        """Test validador combinado con documento inválido"""
        with self.assertRaises(serializers.ValidationError):
            validate_dni_nie_nif_serializer("INVALID")


class NormalizeDocumentoTestCase(TestCase):
    """Tests para normalización de documentos"""

    def test_normalize_documento_mayusculas(self):
        """Test normalización a mayúsculas"""
        result = normalize_documento("12345678z")
        self.assertEqual(result, "12345678Z")

    def test_normalize_documento_espacios(self):
        """Test normalización elimina espacios"""
        result = normalize_documento("  12345678Z  ")
        self.assertEqual(result, "12345678Z")

    def test_normalize_documento_vacio(self):
        """Test normalización de string vacío"""
        result = normalize_documento("")
        self.assertEqual(result, "")

    def test_normalize_documento_none(self):
        """Test normalización de None"""
        result = normalize_documento(None)
        self.assertEqual(result, "")


class DNICalculoLetraTestCase(TestCase):
    """Tests específicos para el cálculo de letra de DNI"""

    def test_dni_casos_conocidos(self):
        """Test con casos conocidos de DNI válidos"""
        casos_validos = [
            "00000000T",
            "12345678Z",
            "87654321X",
            "11111111H",
            "99999999R",
        ]
        for dni in casos_validos:
            is_valid, error = validate_dni_format(dni)
            self.assertTrue(is_valid, f"DNI {dni} debería ser válido pero falló: {error}")

    def test_dni_casos_invalidos_letra(self):
        """Test con casos de DNI con letra incorrecta"""
        casos_invalidos = [
            "00000000A",  # Debería ser T
            "12345678A",  # Debería ser Z
            "87654321A",  # Debería ser X
        ]
        for dni in casos_invalidos:
            is_valid, error = validate_dni_format(dni)
            self.assertFalse(is_valid, f"DNI {dni} debería ser inválido")


class NIECalculoLetraTestCase(TestCase):
    """Tests específicos para el cálculo de letra de NIE"""

    def test_nie_casos_conocidos_x(self):
        """Test con casos conocidos de NIE con X"""
        # X se reemplaza por 0
        casos_validos = [
            "X0000000T",  # 0 % 23 = 0 -> T
            "X2345678T",  # 2345678 % 23 = 21 -> K
        ]
        for nie in casos_validos:
            is_valid, error = validate_nie_format(nie)
            self.assertTrue(is_valid, f"NIE {nie} debería ser válido pero falló: {error}")

    def test_nie_casos_conocidos_y(self):
        """Test con casos conocidos de NIE con Y"""
        # Y se reemplaza por 1
        casos_validos = [
            "Y1111111H",
        ]
        for nie in casos_validos:
            is_valid, error = validate_nie_format(nie)
            self.assertTrue(is_valid, f"NIE {nie} debería ser válido pero falló: {error}")

    def test_nie_casos_conocidos_z(self):
        """Test con casos conocidos de NIE con Z"""
        # Z se reemplaza por 2
        casos_validos = [
            "Z1234567R",  # 21234567 % 23 = 1 -> R
        ]
        for nie in casos_validos:
            is_valid, error = validate_nie_format(nie)
            self.assertTrue(is_valid, f"NIE {nie} debería ser válido pero falló: {error}")
