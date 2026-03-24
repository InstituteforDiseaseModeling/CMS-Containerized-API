"""
Simplified CMS wrapper
"""
import subprocess
import pandas as pd
from pathlib import Path

from emodl_validator import is_valid_emodl
from schemas import SEIRModel, SimulationConfig, SimulationResults, AggregationConfig
from emodl_validator import is_valid_emodl

def run_simulation(model: SEIRModel, config: SimulationConfig) -> SimulationResults:
    """Run CMS simulation using compartments.exe in the bin folder"""
    return _run_simulation(model.to_emodl(), config)


def run_emodl_simulation(emodl: str, config: SimulationConfig) -> SimulationResults:
    """Run CMS simulation using compartments.exe in the bin folder"""
    is_valid, error = is_valid_emodl(emodl)
    if not is_valid:
        return SimulationResults(
            trajectories={},
            metadata={},
            success=False,
            error_message=f"Invalid EMODL content: {error}"
        )
    return _run_simulation(emodl, config)




def _run_simulation(emodl: str, config: SimulationConfig) -> SimulationResults:
    """Run CMS simulation using compartments.exe in the bin folder"""
    
    # Get compartments.exe from the bin folder (same directory level)
    bin_dir = Path(__file__).parent / "bin"
    cms_executable = bin_dir / "compartments.exe"
    current_dir = Path(__file__).parent
    
    try:
        # Write model and config files to current directory
        model_file = current_dir / "model.emodl"
        config_file = current_dir / "config.cfg"
        
        model_file.write_text(emodl)
        config_file.write_text(config.to_config_json())
        print("Wrote to ", model_file, config_file)
        # Build command for execution (use Wine if available)
        import os
        import shutil
        
        # Check if we're in a Linux environment and Wine is available
        wine_available = shutil.which('wine')
        is_linux = os.name == 'posix' and not os.path.exists('C:\\')
        
        if is_linux and wine_available:
            # Running in Linux container with Wine
            wine_cmd = 'wine'
            cmd = [
                "xvfb-run", "-a", wine_cmd,
                str(cms_executable),
                "--model", str(model_file),
                "--config", str(config_file)
            ]
            print(f"Using Wine: {wine_cmd}")
        else:
            # Running natively (Windows or local development)
            cmd = [
                str(cms_executable),
                "--model", str(model_file),
                "--config", str(config_file)
            ]
            print("Running natively")
        
        print(f"Running command: {' '.join(cmd)}")
        
        # Run CMS executable from bin directory so it can find supporting DLLs
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=300,  # 5 minute timeout
            cwd=bin_dir  # Run from bin directory to find supporting files
        )
        
        print(f"Return code: {result.returncode}")
        print(f"STDOUT: {result.stdout}")
        print(f"STDERR: {result.stderr}")
        
        # List files in current directory to see what was created
        print("Files in current directory after CMS run:")
        for file in current_dir.iterdir():
            print(f"  {file.name}")
        
        if result.returncode != 0:
            error_msg = result.stderr or result.stdout or "Unknown CMS error"
            return SimulationResults(
                trajectories={},
                metadata={},
                success=False,
                error_message=f"CMS execution error: {error_msg}"
            )
        
        # Read results from bin directory (where CMS actually runs and writes output)
        output_file = bin_dir / f"{config.output_prefix}.csv"
        print(f"Looking for output file: {output_file}")
        if output_file.exists():
            # Read CSV with time columns as headers and compartments as rows
            df = pd.read_csv(output_file, skiprows=1, index_col=0)
            # Transpose so time is the index and compartments are columns
            df_transposed = df.T
            # Ensure time index is numeric
            df_transposed.index = df_transposed.index.astype(float)
            print(config.aggs)
            # Handle aggregation if specified and multiple runs
            if config.aggs and config.runs > 1:
                print(f"Aggregating {config.runs} runs with {config.aggs.type}")
                print(f"Original columns: {list(df_transposed.columns)[:10]}...")  # Show first 10
                
                # Group columns by run index (e.g., S{0}, S{1}, etc.)
                runs_data = {}
                for col in df_transposed.columns:
                    # Extract base compartment name (remove {run_index})
                    if '{' in col and '}' in col:
                        base_name = col.split('{')[0]
                        run_idx = int(col.split('{')[1].split('}')[0])
                        
                        if base_name not in runs_data:
                            runs_data[base_name] = {}
                        runs_data[base_name][run_idx] = df_transposed[col].tolist()
                
                print(f"Found compartments: {list(runs_data.keys())}")
                print(f"Runs per compartment: {[len(v) for v in runs_data.values()][:5]}")
                
                # Convert to format expected by aggregate_results
                trajectories_for_agg = {}
                for compartment, run_dict in runs_data.items():
                    # Sort by run index and extract values
                    sorted_runs = [run_dict[i] for i in sorted(run_dict.keys())]
                    trajectories_for_agg[compartment] = sorted_runs
                
                # Apply aggregation
                trajectories = SimulationResults.aggregate_results(trajectories_for_agg, config.aggs)
                print(f"Aggregated columns: {list(trajectories.keys())}")
                
                metadata = {
                    "duration": config.duration,
                    "runs": config.runs,
                    "aggregation": config.aggs.model_dump(),
                    "original_columns_count": len(df_transposed.columns),
                    "aggregated_columns_count": len(trajectories)
                }
            else:
                # No aggregation - return raw results
                trajectories = df_transposed.to_dict()
                metadata = {
                    "duration": config.duration,
                    "runs": config.runs
                }
            
            # Always print response size before returning
            import json
            response_size = len(json.dumps(trajectories))
            print(f"Final response JSON size: {response_size:,} chars")
            print(f"Number of trajectory keys: {len(trajectories)}")
            
            return SimulationResults(
                trajectories=trajectories,
                metadata=metadata,
                success=True
            )
        else:
            return SimulationResults(
                trajectories={},
                metadata={},
                success=False,
                error_message=f"Output file not found: {output_file}"
            )
            
    except subprocess.TimeoutExpired:
        return SimulationResults(
            trajectories={},
            metadata={},
            success=False,
            error_message="CMS simulation timed out"
        )
    except Exception as e:
        return SimulationResults(
            trajectories={},
            metadata={},
            success=False,
            error_message=f"Unexpected error: {str(e)}"
        )