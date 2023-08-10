import json
import pyodbc
from modules import preprocessing, wc_analytics, driver_analytics
import os 
import pandas as pd

global_data = {}

def loadData():
    appsettings_config = {'port':8050}
    # Load in the SQL Config
    appsettings_config_fp = './configs/appsettings.json'
    if os.path.exists(appsettings_config_fp):
        with open(appsettings_config_fp, 'r') as file:
            appsettings_config = json.load(file)

    # Load in the SQL Config
    sql_config_fp = './configs/sql_config.json'
    with open(sql_config_fp, 'r') as file:
        sql_config = json.load(file)

    # Point to the SQL server and make a SQL querry for the tasks dataset
    cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='
                        + sql_config['server']
                        + ';DATABASE='
                        + sql_config['database']
                        + ';UID='
                        + sql_config['user']
                        + ';PWD='
                        + sql_config['pass'])
    cursor = cnxn.cursor()

    query = """
    SELECT t.TaskId             AS [Task #],
        u.UserName           AS Driver,
        f.ForkliftName       AS Forklift,
        w.WorkcenterCode     AS Workcenter,
        t.PartNo             AS [Part No],
        CASE t.Status
            WHEN 1 THEN 'Waiting'
            WHEN 2 THEN 'In-Progress'
            ELSE 'Completed'
        END                  AS Status,
        CASE t.taskType
            WHEN 1 THEN 'F/G Put Away'
            WHEN 2 THEN 'Replenishment'
            WHEN 3 THEN 'Part Return'
            WHEN 4 THEN 'FG Return'
            WHEN 5 THEN 'Container Move'
            ELSE ''
        END                  AS Name, 
        t.CreationTime       AS [Creation Time],
        t.StartTime          AS [Start Time],
        t.EndTime            AS [End Time],
        t.Distance
    FROM Task t
        INNER JOIN [User] u
                ON t.AssignUserId = u.UserId
        INNER JOIN Workcenter w
                ON t.WorkcenterKey = w.WorkcenterKey
        LEFT JOIN Forklift f
                ON t.TagId = f.TagId
    """
    # Execute SQL querry and preprocess the tasks dataset
    tasks = pd.read_sql(query, cnxn)
    cursor.close()
    tasks = preprocessing.preprocess_task_data(tasks)

    # Load in Markdown File
    md_filepath = './assets/reading_guide_md.txt'
    with open(md_filepath, encoding = 'utf-8') as f:
        reading_guide_md = f.read()


    driver_colors = driver_analytics.assign_driver_colors(tasks)

    # Collect Key Values
    latest_date = tasks['Creation Time'].iloc[0].replace(hour=0, minute=0, second=0, microsecond=0)
    end_dates = {'Full History': pd.to_datetime('2000-01-01', format='%Y-%m-%d'),
                'Past 365-Days': latest_date - pd.Timedelta(365, unit='D'),
                'Past 90-Days': latest_date - pd.Timedelta(90, unit='D'),
                'Past 60-Days': latest_date - pd.Timedelta(60, unit='D'),
                'Past 30-Days': latest_date - pd.Timedelta(30, unit='D')}
    rollover_periods = {'2-Hours': 7200,  # Time in seconds
                        '1.5-Hours': 5400,
                        '1-Hour': 3600,               
                        '30-Mins': 1800,
                        '15-Mins': 900}     
    stat_block_values = wc_analytics.generate_stat_block_values(tasks)

    global_data['driver_colors'] = driver_colors
    global_data['end_dates'] = end_dates
    global_data['rollover_periods'] = rollover_periods
    global_data['tasks'] = tasks
    return (appsettings_config,stat_block_values, reading_guide_md)