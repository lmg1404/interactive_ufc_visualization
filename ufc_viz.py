import pandas as pd
from bokeh.plotting import figure, output_file, show, save
from bokeh.layouts import column, row
from bokeh.models.tools import HoverTool
from bokeh.models.widgets import Select
from bokeh.models import (ColumnDataSource, RadioButtonGroup, GroupFilter, Column, Row, Div, HoverTool, MultiChoice)
from bokeh.io import curdoc, output_notebook
from bokeh.application.handlers.function import FunctionHandler
from bokeh.application import Application

def get_dataframe() -> pd.DataFrame: 
    """Gets the data we will be using and cleans it for use"""
    
    data = pd.read_csv('masterdataframe.csv')
    data['date'] = pd.to_datetime(data['date'])
    data['colors'] = ['#FF3131' if category == 0 else '#1F51FF' for category in data['result']]
    data['result'].replace({0:'Loss', 1:'Win'}, inplace=True)
    data = data[data['time_format'].isin(['5-5-5-5-5', '5-5-5'])]
    
    return data

data = get_dataframe()
data

# vars
fighter_list = sorted(list(data['fighter'].unique()))
stats = list(data.columns[21:42])  # we don't care about accuracies, everything else is some sort of aggregation of these columns
method_options = list(data['method'].unique())
division_list = list(data['division'].unique())
stat_map = {}
for stat in stats:
    stat_map[" ".join(word.capitalize() for word in stat.split("_"))] = stat
    
# make input objects
output_file(filename="custom_filename.html", title="Static HTML file")
title = Div(text='<h1 style="text-align: center">UFC Interactive Scatterplot Viz</h1>')
fighter_button = MultiChoice(title="Fighter(s)", options=fighter_list, option_limit=3, width=250)
stats_axis = Select(title="Y-Axis", options=sorted(stat_map.keys()), value='Sig Strikes Landed')
method = Select(title="Method", options=["Any"] + method_options, value="Any")
division = Select(title="Division", options=["All"] + division_list, value="All")
win_or_loss = RadioButtonGroup(labels=["Any", "Wins", "Losses"], active=0, styles={"padding-top": "20px"})

TOOLTIPS = [
        ('Fighter', '@fighter'),
        ('Opponent', '@opponent'),
        ('Result', '@result'),
        ('Method', '@method'),
        ('Date', '@date'),
        ('Round', '@round'),
        ('Time', '@time')
        ]

source = ColumnDataSource(data=dict(date=[], y=[], color=[], fighter=[], opponent=[], result=[], method=[], round=[], time=[]))

p = figure(height=600, title="", toolbar_location=None, sizing_mode="stretch_width", x_axis_type='datetime')
p.add_tools(HoverTool(tooltips=TOOLTIPS))
p.circle(x="date", y="y", source=source, size=7, color="color", legend_field='result')

def select_points() -> pd.DataFrame():
    if fighter_button.value:
        df = data[data['fighter'].isin(fighter_button.value)] # in a select, but we only are selecting fighters
    else:
        df = data
        
    if method.value != "Any":
        df = df[df['method'] == method.value]
        
    if division.value != "All":
        df = df[df['division'] == division.value]

    if win_or_loss.active == 1:
        df = df[df['result'] == 'Win']

    if win_or_loss.active == 2:
        df = df[df['result'] == 'Loss']
        
    return df

def update():
    df = select_points()
    x_name = "Date"
    y_name = stat_map[stats_axis.value]

    p.xaxis.axis_label = "Date"
    p.yaxis.axis_label = stats_axis.value

    if fighter_button.value:
        p.title.text = f"{len(df)} Bouts of {stats_axis.value} by " + " ".join(fighter for fighter in fighter_button.value) + f" by {method.value} in {division.value} division"
    else:
        p.title.text = f"{len(df)} Bouts of {stats_axis.value} by all Fighters by {method.value} in {division.value} division"
    source.data = dict(
        date=df['date'],
        y=df[y_name],
        color=df['colors'],
        fighter=df['fighter'],
        opponent=df['opponent'],
        result=df['result'],
        method=df['method'],
        round=df['round'],
        time=df['time']
    )
    
controls = [fighter_button, stats_axis, method, division]
for control in controls:
    control.on_change('value', lambda attr, old, new: update())
win_or_loss.on_change('active', lambda attr, old, new: update())

inputs = row(*controls, win_or_loss,  width=320)
update()
layout = column(title, p, inputs, sizing_mode="stretch_width", height=800)

curdoc().add_root(layout)
