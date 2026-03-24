from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict
from typing import Optional, Dict, Any, List, Union, Literal
import json
from datetime import datetime

class SEIRParameters(BaseModel):
    """SEIR model parameters with validation"""
    transmission_rate: float = Field(gt=0, le=10, default=0.3, description="Beta: transmission rate")
    exposure_rate: float = Field(gt=0, le=1, default=0.2, description="Sigma: rate from exposed to infectious") 
    recovery_rate: float = Field(gt=0, le=1, default=0.1, description="Gamma: recovery rate")
    waning_rate: float = Field(ge=0, le=1, default=0.0, description="Rate of immunity waning")
    
    @field_validator('transmission_rate')
    @classmethod
    def validate_transmission_rate(cls, v):
        if v > 5:  # Reasonable upper bound
            raise ValueError('Transmission rate seems unrealistically high')
        return v


class SEIRPopulation(BaseModel):
    """Initial population compartments"""
    susceptible: int = Field(gt=0, default=1000, description="Initial susceptible population")
    exposed: int = Field(ge=0, default=5, description="Initial exposed population") 
    infected: int = Field(ge=0, default=10, description="Initial infected population")
    recovered: int = Field(ge=0, default=0, description="Initial recovered population")
    
    @model_validator(mode='after')
    def validate_infected_or_exposed(self):
        if self.infected == 0 and self.exposed == 0:
            raise ValueError('Must have at least some infected or exposed individuals')
        return self
    
    @property
    def total_population(self) -> int:
        return self.susceptible + self.exposed + self.infected + self.recovered


class SEIRModel(BaseModel):
    """Complete SEIR model specification"""
    name: str = Field(default="seir_model", description="Model name")
    population: SEIRPopulation
    parameters: SEIRParameters
    
    def to_emodl(self) -> str:
        """Generate EMODL file content"""
        return f"""(import (rnrs) (emodl cmslib))

                (start-model "{self.name}")

                (species S {self.population.susceptible})
                (species E {self.population.exposed})
                (species I {self.population.infected})
                (species R {self.population.recovered})
                (species CI 0)

                (param beta {self.parameters.transmission_rate})
                (param sigma {self.parameters.exposure_rate})
                (param gamma {self.parameters.recovery_rate})
                (param waning {self.parameters.waning_rate})

                (reaction infection (S) (E CI) (/ (* beta S I) (+ S E I R)) 0)
                (reaction progression (E) (I) (* sigma E) 0)
                (reaction recovery (I) (R) (* gamma I) 0)
                (reaction waning (R) (S) (* waning R) 0)

                (observe S S)
                (observe E E)
                (observe I I)
                (observe R R)
                (observe cumulative CI)
                (observe population (+ S E I R))

                (end-model)"""


class AggregationConfig(BaseModel):
    """Configuration for aggregating multiple simulation runs"""
    type: Literal["mean", "median", "quantile"] = Field(description="Type of aggregation")
    quantiles: Optional[List[float]] = Field(
        default=None, 
        description="Quantile values (0-1) when type is 'quantile'"
    )
    
    @model_validator(mode='after')
    def validate_quantiles(self):
        if self.type == "quantile":
            if not self.quantiles:
                raise ValueError("quantiles must be provided when type is 'quantile'")
            if any(q < 0 or q > 1 for q in self.quantiles):
                raise ValueError("quantiles must be between 0 and 1")
        return self


class SimulationConfig(BaseModel):
    """Simulation configuration with validation"""
    solver: str = Field(default="SSA", pattern="^(SSA|TAU|RSSA)$")
    runs: int = Field(gt=0, le=1000, default=1, description="Number of realizations")
    duration: float = Field(gt=0, le=10000, description="Simulation duration")
    samples: int = Field(gt=0, le=10000, description="Number of time points to sample")
    random_seed: Optional[int] = Field(default=None, description="Random seed for reproducibility")
    output_prefix: str = Field(default="simulation_results", description="Output file prefix")
    aggs: Optional[AggregationConfig] = Field(default=None, description="Aggregation configuration for multiple runs")
    
    @model_validator(mode='after')
    def validate_samples_duration(self):
        if self.samples > self.duration * 10:  # Reasonable sampling rate
            raise ValueError('Too many samples for the duration')
        return self
    
    def to_config_json(self) -> str:
        """Generate configuration JSON"""
        config = {
            "solver": self.solver,
            "runs": self.runs,
            "duration": self.duration,
            "samples": self.samples + 1,  # CMS expects samples + 1
            "output": {
                "prefix": self.output_prefix
            }
        }
        if self.random_seed:
            config["prng_seed"] = self.random_seed
        return json.dumps(config, indent=2)


class SimulationResults(BaseModel):
    """Structured simulation results"""
    model_config = ConfigDict(arbitrary_types_allowed=True)

    trajectories: Any  # Will be pandas DataFrame in practice
    metadata: Dict[str, Any]
    success: bool
    error_message: Optional[str] = None
    
    @staticmethod
    def aggregate_results(trajectories_dict: Dict, agg_config: AggregationConfig) -> Dict:
        """
        Aggregate multiple simulation runs according to the aggregation configuration.
        
        Args:
            trajectories_dict: Dict where keys are compartment names, values are lists of time series (one per run)
            agg_config: Configuration specifying how to aggregate
            
        Returns:
            Dict with same keys but aggregated values
        """
        import pandas as pd
        import numpy as np
        
        aggregated = {}
        
        for compartment, runs_data in trajectories_dict.items():
            if not runs_data or len(runs_data) == 0:
                aggregated[compartment] = []
                continue
                
            # Convert to DataFrame where each column is a run
            df = pd.DataFrame(runs_data).T  # Transpose so each column is a run
            
            if agg_config.type == "mean":
                aggregated[compartment] = df.mean(axis=1).tolist()
            elif agg_config.type == "median":
                aggregated[compartment] = df.median(axis=1).tolist()
            elif agg_config.type == "quantile":
                # Create columns for each quantile
                for q in agg_config.quantiles:
                    key = f"{compartment}_q{q:.3f}".replace(".", "")
                    aggregated[key] = df.quantile(q, axis=1).tolist()
            
        return aggregated
    
    def plot(self, compartments: List[str] = None, title: str = "SEIR Results") -> Any:
        """
        Simple plot of simulation results.
        
        Args:
            compartments: List of compartments to plot (default: S, E, I, R)
            title: Plot title
        """
        import matplotlib.pyplot as plt
        import pandas as pd
        
        if not self.success:
            raise ValueError(f"Cannot plot failed simulation: {self.error_message}")
        
        # Convert dict back to DataFrame for plotting
        df = pd.DataFrame(self.trajectories)
        
        # Default to main compartments
        if compartments is None:
            compartments = ['S{0}', 'E{0}', 'I{0}', 'R{0}']
        
        # Simple plot
        fig, ax = plt.subplots(figsize=(10, 6))
        
        for comp in compartments:
            if comp in df.columns:
                label = comp.replace('{0}', '')
                ax.plot(df.index, df[comp], label=label, linewidth=2)
        
        ax.set_xlabel('Time')
        ax.set_ylabel('Population')
        ax.set_title(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.close(fig)  # Prevent double display
        return fig
    
    def get_peak_infection(self) -> tuple:
        """Get peak infection count and when it occurred."""
        import pandas as pd
        
        # Convert dict back to DataFrame for analysis
        df = pd.DataFrame(self.trajectories)
        if 'I{0}' in df.columns:
            peak_value = df['I{0}'].max()
            peak_time = df['I{0}'].idxmax()
            return peak_time, peak_value
        return None, None