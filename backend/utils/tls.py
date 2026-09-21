from pathlib import Path
import os


def load_certificates() -> str | None:
    """
    Construye un bundle de certificados CA para
    validar la conexión TLS con Datacrédito.
    """

    certificates: list[str] = []

    paths = [
        os.getenv("DATACREDITO_CA_ROOT"),
        os.getenv("DATACREDITO_CA_EV"),
        os.getenv("DATACREDITO_CA_OV"),
    ]

    for path in paths:

        if not path:
            continue

        certificate_path = Path(path)

        if certificate_path.exists():
            certificates.append(
                certificate_path.read_text(
                    encoding="utf-8"
                )
            )

    if not certificates:
        return None

    return "\n".join(certificates)