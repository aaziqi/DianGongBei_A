import pandas as pd

# 读取负荷数据
load_data = pd.read_excel('附件1：各园区典型日负荷数据.xlsx')
# 读取风光发电数据
generation_data = pd.read_excel('附件2_new.xlsx')

# 确保时间列不会影响计算
load_data.set_index('时间（h）', inplace=True)
generation_data.set_index('时间（h）', inplace=True)

# 打印列名以确认
print("Load data columns:", load_data.columns)
print("Generation data columns:", generation_data.columns)

# 负荷增长50%
load_data_grown = load_data * 1.5

# 计算每个园区需要的风电和光伏装机容量
def calculate_capacity(load_data, generation_data, wind_cost_per_kw, solar_cost_per_kw):
    capacity = {}
    for park in load_data.columns:
        if 'Load' in park:
            max_load = load_data[park].max()
            park_name = park.split('_')[1]
            wind_col = park_name + '_Wind'
            solar_col = park_name + '_Solar'
            
            wind_gen = generation_data[wind_col].sum()
            solar_gen = generation_data[solar_col].sum()
            
            # 避免除以零的情况
            if wind_gen == 0:
                wind_gen = 1e-9  # 设为一个非常小的数以避免除以零
            if solar_gen == 0:
                solar_gen = 1e-9  # 设为一个非常小的数以避免除以零

            required_wind_capacity = max_load / (wind_gen * wind_cost_per_kw)
            required_solar_capacity = max_load / (solar_gen * solar_cost_per_kw)
            
            capacity[park_name] = {
                'wind': required_wind_capacity,
                'solar': required_solar_capacity
            }
    return capacity

# 计算储能系统容量
def calculate_storage_capacity(load_data, storage_power_cost, storage_energy_cost, min_soc=0.1, max_soc=0.9):
    storage = {}
    for park in load_data.columns:
        if 'Load' in park:
            max_load = load_data[park].max()
            park_name = park.split('_')[1]
            # 假设储能容量应满足日最大负荷波动的50%
            storage_power = max_load * 0.8  # SOC变化范围乘以最大负荷
            storage_energy = storage_power * (max_soc + min_soc) / 2  # 假设SOC变化平均为(SOC上限+SOC下限)/2
            
            storage[park_name] = {
                'power': storage_power,
                'energy': storage_energy,
                'cost': storage_power * storage_power_cost + storage_energy * storage_energy_cost
            }
    return storage

# 计算购电量和弃风弃光电量
def calculate_purchase_and_abandonment(load_data, generation_data):
    purchase = {}
    abandonment = {}
    for park in load_data.columns:
        if 'Load' in park:
            park_name = park.split('_')[1]
            wind_col = park_name + '_Wind'
            solar_col = park_name + '_Solar'
            
            total_load = load_data[park].sum()
            total_wind_gen = generation_data[wind_col].sum()
            total_solar_gen = generation_data[solar_col].sum()
            total_gen = total_wind_gen + total_solar_gen
            
            purchase[park_name] = max(0, total_load - total_gen)
            abandonment[park_name] = max(0, total_gen - total_load)
            
    return purchase, abandonment

# 计算自发电成本
def calculate_self_generation_cost(generation_data, wind_cost_per_kwh=0.5, solar_cost_per_kwh=0.4):
    self_gen_cost = {}
    for col in generation_data.columns:
        if 'Wind' in col:
            park_name = col.split('_')[0]
            wind_gen = generation_data[col].sum()
            self_gen_cost[park_name + '_Wind'] = wind_gen * wind_cost_per_kwh
        elif 'Solar' in col:
            park_name = col.split('_')[0]
            solar_gen = generation_data[col].sum()
            self_gen_cost[park_name + '_Solar'] = solar_gen * solar_cost_per_kwh
            
    return self_gen_cost

# 计算购电成本
def calculate_purchase_cost(purchase, purchase_cost_per_kwh=1):
    purchase_cost = {}
    for park in purchase:
        purchase_cost[park] = purchase[park] * purchase_cost_per_kwh
    return purchase_cost

# 计算总供电成本
def calculate_total_supply_cost(self_gen_cost, purchase_cost):
    total_cost = 0
    for cost in self_gen_cost.values():
        total_cost += cost
    for cost in purchase_cost.values():
        total_cost += cost
    return total_cost

# 计算储能系统成本
def calculate_storage_cost(storage_capacity, storage_power_cost, storage_energy_cost):
    total_storage_cost = 0
    for park in storage_capacity:
        total_storage_cost += storage_capacity[park]['cost']
    return total_storage_cost

# 定义单价
wind_cost_per_kw = 3000
solar_cost_per_kw = 2500
storage_power_cost = 800
storage_energy_cost = 1800

# 计算装机容量和储能系统容量
capacity = calculate_capacity(load_data_grown, generation_data, wind_cost_per_kw, solar_cost_per_kw)
print("Capacity:", capacity)

storage_capacity = calculate_storage_capacity(load_data_grown, storage_power_cost, storage_energy_cost)
print("Storage capacity:", storage_capacity)

# 计算购电量和弃风弃光电量
purchase, abandonment = calculate_purchase_and_abandonment(load_data_grown, generation_data)
print("Purchase:", purchase)
print("Abandonment:", abandonment)

# 计算自发电成本
self_gen_cost = calculate_self_generation_cost(generation_data)
print("Self Generation Cost:", self_gen_cost)

# 计算购电成本
purchase_cost = calculate_purchase_cost(purchase)
print("Purchase Cost:", purchase_cost)

# 计算总供电成本
total_supply_cost = calculate_total_supply_cost(self_gen_cost, purchase_cost)
print(f"Total Supply Cost: {total_supply_cost}元")

# 计算储能系统成本
storage_cost = calculate_storage_cost(storage_capacity, storage_power_cost, storage_energy_cost)
print(f"Storage Cost: {storage_cost}元")

# 总成本（包含储能系统）
total_cost = total_supply_cost + storage_cost
print(f"总成本为：{total_cost}元")

# 经济性分析
def economic_analysis(total_cost, payback_period):
    annualized_cost = total_cost / payback_period
    return annualized_cost

annualized_cost = economic_analysis(total_cost, 5)
print(f"总年化成本为：{annualized_cost}元")

# 计算联合园区的光伏装机容量和风电装机容量
total_wind_capacity = sum([capacity[park]['wind'] for park in capacity]) / 1000
total_solar_capacity = sum([capacity[park]['solar'] for park in capacity]) / 1000

print(f'联合园区的光伏装机容量为：{total_solar_capacity} KW')
print(f'联合园区的风电装机容量为：{total_wind_capacity} KW')