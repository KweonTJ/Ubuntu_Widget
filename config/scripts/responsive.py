"""Pure size metrics shared by Eww bindings and layout regression checks."""
def metrics(width, height):
    width, height = max(96, int(width)), max(64, int(height))
    clamp = lambda value, low, high: round(max(low, min(high, value)))
    mode = 'small' if height < 168 or width < 248 else 'large' if height >= 300 and width >= 360 else 'medium'
    padding = clamp(min(width, height) * .075, 10, 24)
    content_height = height - 16 - padding * 2
    # Weather uses one aligned summary, not a floating corner decoration.
    weather_city = clamp(width/28,12,17)
    weather_detail = max(11,clamp(width/31,10,13))
    weather_gap = clamp(height*.025,4,10)
    weather_width = width-16-padding*2-2  # canvas and card border
    # Allow for the taller line boxes of the Korean fallback font.
    weather_budget = content_height-2
    if height>=112:weather_budget -= weather_city*1.8+weather_gap
    if height>=144:weather_budget -= weather_detail*1.8+weather_gap
    if height>=272:weather_budget -= 48+weather_gap
    weather_icon = clamp(min(weather_width*(.42 if width<280 else .34),weather_budget),32,128)
    base_hero = clamp(min((width-padding*2)*.23,content_height*.43),22,76)
    weather_temperature = clamp(min(max(base_hero*1.2,weather_budget*.72),
                                    (weather_width-weather_icon-weather_gap)/2.3,weather_budget/1.8),24,88)
    music_gap=clamp(height*.02,3,8)
    music_detail=max(11,clamp(width/31,10,13))
    # The cover gets the remaining height above the title and optional controls.
    music_budget=content_height-2-clamp(width/23,12,19)*1.8-music_gap
    if height>=200:music_budget-=music_detail*1.8+3
    if height>=240:music_budget-=34+music_gap
    music_art=clamp(min(width-16-padding*2-2,music_budget),24,256)
    return {'width': width, 'height': height, 'mode': mode, 'padding': padding,
            'hero': clamp(min((width-padding*2)*.23, content_height*.43), 22, 76),
            'clock': clamp(min((width-padding*2)/3.1, content_height*.52), 24, 84),
            'title': clamp(width/23, 12, 19), 'body': clamp(width/28, 11, 15),
            'detail': clamp(width/31, 10, 13), 'gap': clamp(height*.04, 4, 14),
            'face': clamp(min(width-16-padding*2, content_height-(42 if height>=145 else 0)),32,220),
            'weather_icon': weather_icon, 'weather_temperature': weather_temperature,
            'weather_city': weather_city, 'weather_detail': weather_detail, 'weather_gap': weather_gap,
            # Fit a full daily duration such as 23시간 59분, including Korean units.
            'screen_time': clamp(min((width-16-padding*2-2)/6, content_height*.43), 18, 68),
            'music_art': music_art, 'music_gap': music_gap, 'music_detail': music_detail,
            'art': clamp(min(width*.21, content_height*.45), 32, 96),
            'battery_ring': clamp(min((width-16-padding*2)/3-8, content_height-24) if height<160 else min((width-16-padding*2)/2-12, (content_height-42)/2), 36, 84),
            'ring': clamp(min(width*.2, content_height*.28), 36, 90),
            'cell': clamp(min((width-16-padding*2)/7, (content_height-38)/6), 12, 42),
            'day_font': clamp(min((width-16-padding*2)/10, (content_height-38)/9), 9, 18),
            'rows': max(1, (height-100)//36), 'hours': 3 if width < 280 else 4 if width < 400 else 6}
