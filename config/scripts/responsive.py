"""Pure size metrics shared by Eww bindings and layout regression checks."""
def metrics(width, height):
    width, height = max(96, int(width)), max(64, int(height))
    clamp = lambda value, low, high: round(max(low, min(high, value)))
    mode = 'small' if height < 168 or width < 248 else 'large' if height >= 300 and width >= 360 else 'medium'
    padding = clamp(min(width, height) * .075, 10, 24)
    content_height = height - 16 - padding * 2
    return {'width': width, 'height': height, 'mode': mode, 'padding': padding,
            'hero': clamp(min((width-padding*2)*.23, content_height*.43), 22, 76),
            'clock': clamp(min((width-padding*2)/3.1, content_height*.52), 24, 84),
            'title': clamp(width/23, 12, 19), 'body': clamp(width/28, 11, 15),
            'detail': clamp(width/31, 10, 13), 'gap': clamp(height*.04, 4, 14),
            'face': clamp(min(width-16-padding*2, content_height-(42 if height>=145 else 0)),32,220),
            'art': clamp(min(width*.21, content_height*.45), 32, 96),
            'battery_ring': clamp(min((width-16-padding*2)/3-8, content_height-24) if height<160 else min((width-16-padding*2)/2-12, (content_height-42)/2), 36, 84),
            'ring': clamp(min(width*.2, content_height*.28), 36, 90),
            'cell': clamp(min((width-16-padding*2)/7, (content_height-38)/6), 12, 42),
            'day_font': clamp(min((width-16-padding*2)/10, (content_height-38)/9), 9, 18),
            'rows': max(1, (height-100)//36), 'hours': 3 if width < 280 else 4 if width < 400 else 6}
