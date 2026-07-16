from dataclasses import dataclass
from data.generators.state import BmsTelemetryState


@dataclass
class TelemetryFrame:
    """
    Envelope pattern per i dati di telemetria.
    Contiene lo stato fisico (dominio) e i metadati di acquisizione.
    """
    timestamp: float
    state: BmsTelemetryState
