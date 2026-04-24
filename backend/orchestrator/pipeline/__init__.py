from .step_01_sam import SamGovStep
from .step_02_csl import ConsolidatedScreeningStep
from .step_03_ofac import OfacSdnStep
from .step_04_leie import LeieStep
from .step_05_edgar import SecEdgarStep
from .step_06_irs import IrsTaxExemptStep
from .step_07_sos_home import SosHomeStateStep
from .step_08_sos_states import SosEmployeeStatesStep
from .step_09_nova_search import NovaWebSearchStep
from .step_10_nova_report import NovaReportStep

ALL_STEPS = [
    SamGovStep(),
    ConsolidatedScreeningStep(),
    OfacSdnStep(),
    LeieStep(),
    SecEdgarStep(),
    IrsTaxExemptStep(),
    SosHomeStateStep(),
    SosEmployeeStatesStep(),
    NovaWebSearchStep(),
    NovaReportStep(),
]

__all__ = ["ALL_STEPS"]
