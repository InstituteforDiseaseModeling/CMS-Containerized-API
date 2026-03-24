from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

import simple_cms_wrapper as scw
from schemas import SEIRModel, SimulationConfig, SimulationResults

app = FastAPI()

class SimulationRequest(BaseModel):
    model: SEIRModel
    config: SimulationConfig

@app.post('/run_seir_simulation', response_model=SimulationResults)
def run_seir_simulation(request: SimulationRequest):
    """Run a SEIR model simulation using CMS"""
    try:
        return scw.run_simulation(request.model, request.config)
    except Exception as e:
        return SimulationResults(
            trajectories={},
            metadata={},
            success=False,
            error_message=f"Unexpected error: {str(e)}"
        )
    
class EMODLSimulationRequest(BaseModel):
    emodl: str
    config: SimulationConfig
@app.post('/run_emodl_simulation', response_model=SimulationResults)
def run_emodl_simulation(request: EMODLSimulationRequest):
    """Run a simulation using provided EMODL content and configuration"""
    try:
        return scw.run_emodl_simulation(request.emodl, request.config)
    except Exception as e:
        return SimulationResults(
            trajectories={},
            metadata={},
            success=False,
            error_message=f"Unexpected error: {str(e)}"
        )

if __name__ == '__main__':
    uvicorn.run('api_main:app', reload=True)