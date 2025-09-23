# utils/charts.py
import altair as alt
import pandas as pd
import streamlit as st
from typing import List, Optional, Dict, Any
from .helpers import get_color_by_score

def create_branch_chart(df: pd.DataFrame, title: str = "ביצועי סניפים") -> alt.Chart:
    """יצירת גרף השוואת סניפים"""
    if df.empty:
        return None
    
    branch_stats = df.groupby('branch')['overall_score'].agg(['mean', 'count']).reset_index()
    branch_stats = branch_stats[branch_stats['count'] >= 2]  # מינימום 2 בדיקות
    branch_stats['mean'] = branch_stats['mean'].round(2)
    
    if branch_stats.empty:
        return None
    
    # הוספת צבעים לפי ציון
    branch_stats['color'] = branch_stats['mean'].apply(get_color_by_score)
    
    chart = alt.Chart(branch_stats).mark_bar(
        size=40,
        cornerRadius=4
    ).encode(
        x=alt.X('branch:N', 
                title='סניף', 
                sort='-y',
                axis=alt.Axis(labelAngle=0, labelFontSize=12)),
        y=alt.Y('mean:Q', 
                title='ממוצע ציון', 
                scale=alt.Scale(domain=[0, 10]),
                axis=alt.Axis(titleFontSize=12)),
        color=alt.Color('color:N', scale=None),
        tooltip=[
            alt.Tooltip('branch:N', title='סניף'),
            alt.Tooltip('mean:Q', title='ממוצע', format='.2f'),
            alt.Tooltip('count:Q', title='מספר בדיקות')
        ]
    ).properties(
        width=600,
        height=300,
        title=alt.TitleParams(
            text=title,
            fontSize=14,
            fontWeight='bold'
        )
    ).resolve_scale(
        color='independent'
    )
    
    return chart

def create_trend_chart(df: pd.DataFrame, title: str = "מגמת ציונים") -> alt.Chart:
    """יצירת גרף מגמות זמן"""
    if df.empty or len(df) < 3:
        return None
    
    # קיבוץ לפי יום
    daily_df = df.copy()
    daily_df['date'] = daily_df['created_at'].dt.date
    daily_stats = daily_df.groupby('date')['overall_score'].agg(['mean', 'count']).reset_index()
    daily_stats['date'] = pd.to_datetime(daily_stats['date'])
    daily_stats['mean'] = daily_stats['mean'].round(2)
    
    # קו ממוצע
    line_chart = alt.Chart(daily_stats).mark_line(
        strokeWidth=3,
        color='#10b981',
        point=True
    ).encode(
        x=alt.X('date:T', 
                title='תאריך',
                axis=alt.Axis(format='%d/%m', labelAngle=45)),
        y=alt.Y('mean:Q', 
                title='ממוצע ציון',
                scale=alt.Scale(domain=[0, 10])),
        tooltip=[
            alt.Tooltip('date:T', title='תאריך', format='%d/%m/%Y'),
            alt.Tooltip('mean:Q', title='ממוצע', format='.2f'),
            alt.Tooltip('count:Q', title='בדיקות')
        ]
    )
    
    # קו יעד
    target_line = alt.Chart(pd.DataFrame({'target': [8.0]})).mark_rule(
        color='red',
        strokeDash=[5, 5],
        strokeWidth=2
    ).encode(
        y='target:Q'
    )
    
    chart = (line_chart + target_line).properties(
        width=600,
        height=300,
        title=alt.TitleParams(
            text=title,
            fontSize=14,
            fontWeight='bold'
        )
    )
    
    return chart

def create_score_distribution_chart(df: pd.DataFrame, title: str = "התפלגות ציונים") -> alt.Chart:
    """יצירת גרף התפלגות ציונים"""
    if df.empty:
        return None
    
    score_dist = df['overall_score'].value_counts().reset_index()
    score_dist.columns = ['score', 'count']
    score_dist = score_dist.sort_values('score')
    
    # הוספת צבעים
    score_dist['color'] = score_dist['score'].apply(get_color_by_score)
    
    chart = alt.Chart(score_dist).mark_bar(
        size=30,
        cornerRadius=4
    ).encode(
        x=alt.X('score:O', 
                title='ציון',
                axis=alt.Axis(labelFontSize=12)),
        y=alt.Y('count:Q', 
                title='כמות בדיקות',
                axis=alt.Axis(titleFontSize=12)),
        color=alt.Color('color:N', scale=None),
        tooltip=[
            alt.Tooltip('score:O', title='ציון'),
            alt.Tooltip('count:Q', title='כמות')
        ]
    ).properties(
        width=600,
        height=300,
        title=alt.TitleParams(
            text=title,
            fontSize=14,
            fontWeight='bold'
        )
    ).resolve_scale(
        color='independent'
    )
    
    return chart

def create_dish_performance_chart(df: pd.DataFrame, title: str = "ביצועי מנות") -> alt.Chart:
    """יצירת גרף ביצועי מנות"""
    if df.empty:
        return None
    
    dish_stats = df.groupby('dish_name')['overall_score'].agg(['mean', 'count']).reset_index()
    dish_stats = dish_stats[dish_stats['count'] >= 2]  # מינימום 2 בדיקות
    dish_stats = dish_stats.nlargest(10, 'count')  # 10 המנות הפופולריות
    dish_stats['mean'] = dish_stats['mean'].round(2)
    
    if dish_stats.empty:
        return None
    
    chart = alt.Chart(dish_stats).mark_circle(
        opacity=0.8
    ).encode(
        x=alt.X('mean:Q', 
                title='ממוצע ציון',
                scale=alt.Scale(domain=[0, 10])),
        y=alt.Y('dish_name:N', 
                title='מנה',
                sort='-x'),
        size=alt.Size('count:Q', 
                     title='מספר בדיקות',
                     scale=alt.Scale(range=[100, 500])),
        color=alt.Color('mean:Q',
                       scale=alt.Scale(range=['#ef4444', '#f59e0b', '#eab308', '#10b981']),
                       title='ממוצע'),
        tooltip=[
            alt.Tooltip('dish_name:N', title='מנה'),
            alt.Tooltip('mean:Q', title='ממוצע', format='.2f'),
            alt.Tooltip('count:Q', title='בדיקות')
        ]
    ).properties(
        width=600,
        height=400,
        title=alt.TitleParams(
            text=title,
            fontSize=14,
            fontWeight='bold'
        )
    )
    
    return chart

def create_chef_performance_chart(df: pd.DataFrame, branch: str = None, 
                                title: str = "ביצועי טבחים") -> alt.Chart:
    """יצירת גרף ביצועי טבחים"""
    if df.empty:
        return None
    
    # סינון לפי סניף אם נדרש
    if branch:
        df = df[df['branch'] == branch]
        title = f"{title} - {branch}"
    
    chef_stats = df.groupby('chef_name')['overall_score'].agg(['mean', 'count']).reset_index()
    chef_stats = chef_stats[chef_stats['count'] >= 3]  # מינימום 3 בדיקות
    chef_stats = chef_stats.sort_values('mean', ascending=True)  # מהנמוך לגבוה
    chef_stats['mean'] = chef_stats['mean'].round(2)
    
    if chef_stats.empty:
        return None
    
    # הגבלה ל-15 טבחים
    if len(chef_stats) > 15:
        chef_stats = chef_stats.tail(15)
    
    chart = alt.Chart(chef_stats).mark_bar(
        size=20,
        cornerRadius=2
    ).encode(
        x=alt.X('mean:Q', 
                title='ממוצע ציון',
                scale=alt.Scale(domain=[0, 10])),
        y=alt.Y('chef_name:N', 
                title='טבח',
                sort=None),
        color=alt.Color('mean:Q',
                       scale=alt.Scale(range=['#ef4444', '#f59e0b', '#eab308', '#10b981']),
                       title='ממוצע'),
        tooltip=[
            alt.Tooltip('chef_name:N', title='טבח'),
            alt.Tooltip('mean:Q', title='ממוצע', format='.2f'),
            alt.Tooltip('count:Q', title='בדיקות')
        ]
    ).properties(
        width=600,
        height=max(300, len(chef_stats) * 25),
        title=alt.TitleParams(
            text=title,
            fontSize=14,
            fontWeight='bold'
        )
    )
    
    return chart

def create_weekly_comparison_chart(df: pd.DataFrame, title: str = "השוואה שבועית") -> alt.Chart:
    """יצירת גרף השוואה שבועית"""
    if df.empty or len(df) < 7:
        return None
    
    # חישוב שבועות
    weekly_df = df.copy()
    weekly_df['week'] = weekly_df['created_at'].dt.to_period('W').dt.start_time
    weekly_stats = weekly_df.groupby('week')['overall_score'].agg(['mean', 'count']).reset_index()
    weekly_stats = weekly_stats[weekly_stats['count'] >= 5]  # מינימום 5 בדיקות בשבוע
    weekly_stats['mean'] = weekly_stats['mean'].round(2)
    
    if len(weekly_stats) < 2:
        return None
    
    # עיצוב התאריכים
    weekly_stats['week_display'] = weekly_stats['week'].dt.strftime('%d/%m')
    
    chart = alt.Chart(weekly_stats).mark_line(
        strokeWidth=3,
        color='#10b981',
        point=alt.OverlayMarkDef(size=100, filled=True)
    ).encode(
        x=alt.X('week_display:N', 
                title='שבוע',
                axis=alt.Axis(labelAngle=45)),
        y=alt.Y('mean:Q', 
                title='ממוצע ציון',
                scale=alt.Scale(domain=[0, 10])),
        tooltip=[
            alt.Tooltip('week_display:N', title='שבוע'),
            alt.Tooltip('mean:Q', title='ממוצע', format='.2f'),
            alt.Tooltip('count:Q', title='בדיקות')
        ]
    ).properties(
        width=600,
        height=300,
        title=alt.TitleParams(
            text=title,
            fontSize=14,
            fontWeight='bold'
        )
    )
    
    return chart

def create_combined_dashboard_chart(df: pd.DataFrame) -> alt.Chart:
    """יצירת דשבורד משולב"""
    if df.empty:
        return None
    
    # גרף עליון - מגמה יומית
    trend_chart = create_trend_chart(df, "מגמה יומית")
    
    # גרף תחתון - השוואת סניפים
    branch_chart = create_branch_chart(df, "ביצועי סניפים")
    
    if trend_chart and branch_chart:
        combined = alt.vconcat(
            trend_chart,
            branch_chart
        ).resolve_scale(
            color='independent'
        )
        return combined
    
    return trend_chart or branch_chart
