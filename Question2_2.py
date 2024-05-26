import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 假设已读入数据
load_data = pd.DataFrame({
    '时间（h）': [f'{i:02}:00:00' for i in range(24)],
    'Load': [818, 820, 913, 918, 871, 865, 860, 870, 890, 920, 960, 990, 1000, 980, 950, 930, 900, 880, 850, 830, 810, 800, 790, 780]
})
wind_solar_data = pd.DataFrame({
    '时间（h）': [f'{i:02}:00:00' for i in range(24)],
    'Ppv': [0.0, 0.0, 0.0, 0.0, 0.0, 10.0, 30.0, 50.0, 80.0, 110.0, 130.0, 150.0, 160.0, 150.0, 130.0, 100.0, 70.0, 50.0, 30.0, 10.0, 0.0, 0.0, 0.0, 0.0],
    'Pw': [303.30, 491.55, 494.75, 535.95, 738.70, 600.0, 550.0, 500.0, 450.0, 400.0, 350.0, 300.0, 250.0, 200.0, 150.0, 100.0, 80.0, 60.0, 50.0, 40.0, 30.0, 20.0, 10.0, 5.0]
})

# 整合数据
total_load = load_data['Load']
total_solar = wind_solar_data['Ppv']
total_wind = wind_solar_data['Pw']
total_wind_solar = total_wind + total_solar

# 储能系统参数
storage_capacity = 100  # kWh
storage_power = 50  # kW
soc_max = 0.9
soc_min = 0.1
efficiency = 0.95

# 初始化储能状态
soc = 0.5 * storage_capacity  # 初始SOC设为50%

# 计算电量缺口和过剩
power_deficit = total_load - total_wind_solar
power_surplus = total_wind_solar - total_load

# 储能运行策略
soc_history = []
charge_discharge = []

for i in range(len(total_load)):
    if power_surplus[i] > 0:
        # 有多余电量，充电
        charge_power = min(power_surplus[i], storage_power)
        soc += charge_power * efficiency
        soc = min(soc, storage_capacity * soc_max)
        charge_discharge.append(charge_power)
    else:
        # 电量不足，放电
        discharge_power = min(-power_deficit[i], storage_power)
        soc -= discharge_power / efficiency
        soc = max(soc, storage_capacity * soc_min)
        charge_discharge.append(-discharge_power)
    soc_history.append(soc)

# 计算购电量、弃风弃光电量
total_purchased = sum(max(0, def_val) for def_val in power_deficit)
total_abandoned = sum(max(0, sur_val) for sur_val in power_surplus)

# 计算经济性指标
wind_power_cost = total_wind.sum() * 0.5  # 风电购电成本
solar_power_cost = total_solar.sum() * 0.4  # 光伏购电成本
total_generation_cost = wind_power_cost + solar_power_cost

storage_cost = storage_capacity * 1800 + storage_power * 800  # 储能系统成本
total_cost = total_purchased + storage_cost / 10 / 365  # 假设储能系统使用寿命为10年
average_cost = total_cost / sum(total_load)

# 输出结果
print(f'总购电量: {total_purchased:.2f} kWh')
print(f'总弃风弃光电量: {total_abandoned:.2f} kWh')
print(f'总供电成本: {total_cost:.2f} 元')
print(f'单位电量平均供电成本: {average_cost:.2f} 元/kWh')
print(f'储能系统的容量: {storage_capacity} kWh')
print(f'储能系统的功率: {storage_power} kW')

# 绘制图表
time_labels = load_data['时间（h）']

fig, axs = plt.subplots(3, 1, figsize=(12, 18))

# 总负荷、总风光发电、SOC随时间变化图
axs[0].plot(time_labels, total_load, label='Total Load (kWh)')
axs[0].plot(time_labels, total_wind_solar, label='Total Wind and Solar Generation (kWh)')
axs[0].plot(time_labels, soc_history, label='State of Charge (kWh)')
axs[0].set_title('Load, Generation, and State of Charge over Time')
axs[0].set_xlabel('Time (h)')
axs[0].set_ylabel('Energy (kWh)')
axs[0].legend()

# 总购电量随时间变化图
axs[1].plot(time_labels, charge_discharge, label='Charge/Discharge Power (kWh)', color='orange')
axs[1].set_title('Charge and Discharge Power over Time')
axs[1].set_xlabel('Time (h)')
axs[1].set_ylabel('Energy (kWh)')
axs[1].legend()

# 总购电量与总弃风弃光电量条形图
labels = ['Total Purchased Power', 'Total Abandoned Wind and Solar']
values = [total_purchased, total_abandoned]
axs[2].bar(labels, values, color=['blue', 'green'])
axs[2].set_title('Total Purchased Power and Total Abandoned Wind and Solar')
axs[2].set_ylabel('Energy (kWh)')

plt.tight_layout()
plt.show()