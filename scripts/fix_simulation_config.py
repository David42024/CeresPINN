import re

file_path = "src/components/SimulationConfig.tsx"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

old_code = """  const handleScenarioChange = (scenario: ClimateScenario) => {
    onChangeConfig({ ...config, scenario });
  };

  const handleYearChange = (targetYear: number) => {
    onChangeConfig({ ...config, targetYear });
  };"""

new_code = """  const handleScenarioChange = (scenario: ClimateScenario) => {
    const newForcing = getCMIP6ClimateForcing(scenario, config.targetYear);
    onChangeConfig({ 
      ...config, 
      scenario,
      temperatureAnomalyC: newForcing.tempAnomalyC,
      precipitationAnomalyPercent: newForcing.precipAnomalyPct,
      carbonDioxidePpm: newForcing.co2Ppm
    });
  };

  const handleYearChange = (targetYear: number) => {
    const newForcing = getCMIP6ClimateForcing(config.scenario, targetYear);
    onChangeConfig({ 
      ...config, 
      targetYear,
      temperatureAnomalyC: newForcing.tempAnomalyC,
      precipitationAnomalyPercent: newForcing.precipAnomalyPct,
      carbonDioxidePpm: newForcing.co2Ppm
    });
  };"""

content = content.replace(old_code, new_code)

with open(file_path, "w", encoding="utf-8") as f:
    f.write(content)
print("SimulationConfig.tsx fixed")
