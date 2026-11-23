"""Validación y normalización de textos."""

LETRAS_DNI = "TRWAGMYFPDXBNJZSQVHLCKE"


def esta_vacio(texto: str | None) -> bool:
    """Indica si el texto es ``None``, está vacío o solo contiene espacios.

    >>> esta_vacio("   ")
    True
    >>> esta_vacio(" a ")
    False
    """
    if texto is None:
        return True
    texto = texto.strip()
    return len(texto) == 0


def normalizar_nombre(nombre: str) -> str:
    """Quita los espacios sobrantes y pone en mayúscula la inicial de cada palabra.

    >>> normalizar_nombre("  ada   LOVELACE ")
    'Ada Lovelace'
    """
    return " ".join(nombre.split()).title()

def es_email(texto: str) -> bool:
    """Comprueba de forma sencilla que el texto tiene forma de correo.

    Reglas: no contiene espacios, tiene exactamente una arroba, hay texto
    antes de la arroba, y el dominio contiene al menos un punto que no está
    ni al principio ni al final.

    >>> es_email("ada@ejemplo.com")
    True
    >>> es_email("ada@ejemplo")
    False
    """
    if " " in texto:
        return False
    if texto.count("@") != 1:
        return False

    usuario, dominio = texto.split("@")

    if usuario == "" or dominio == "":
        return False
    if usuario.startswith(".") or usuario.endswith("."):
        return False
    if "." not in dominio:
        return False
    if dominio.startswith(".") or dominio.endswith("."):
        return False
    if ".." in texto:
        return False

    return True


def es_dni(texto: str) -> bool:
    """Comprueba que el texto es un DNI válido: ocho dígitos y la letra correcta.

    La letra se obtiene tomando el resto de dividir el número entre 23 y
    usándolo como posición en ``LETRAS_DNI``. Admite la letra en minúscula y
    espacios alrededor.

    >>> es_dni("12345678Z")
    True
    >>> es_dni("12345678A")
    False
    """
    texto = texto.strip().upper()
    if len(texto) != 9:
        return False
    numero = texto[:8]
    letra = texto[8].upper()

    if not numero.isdigit():
        return False
    
    letra_esperada = LETRAS_DNI[int(numero) % 23]
    if letra != letra_esperada:
        return False
    return True
