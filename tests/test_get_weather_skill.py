
import asyncio
from app.skills.weather import query_weather_data,query_hourly_data,query_forecast_data
result = asyncio.run(query_weather_data('海淀'))
result_h = asyncio.run(query_hourly_data('海淀'))
resul_f = asyncio.run(query_forecast_data('海淀'))
print(result.model_dump())
print(result_h[0].model_dump())
print(resul_f[0].model_dump())