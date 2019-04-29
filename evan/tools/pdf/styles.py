import os

from reportlab.lib.enums import TA_JUSTIFY, TA_RIGHT
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


DIR = os.path.dirname(__file__)

roboto = [
    ['IBMPlexSans-Regular', 'IBMPlexSans-SemiBold', 'IBMPlexSans-Italic', 'IBMPlexSans-SemiBoldItalic'],
    ['IBMPlexSans-Light', 'IBMPlexSans-Medium', 'IBMPlexSans-LightItalic', 'IBMPlexSans-MediumItalic']
]

for fonts in roboto:
    for font in fonts:
        pdfmetrics.registerFont(TTFont(font, os.path.join(DIR, f'fonts/{font}.ttf')))

    pdfmetrics.registerFontFamily(
        fonts[0],
        normal=fonts[0],
        bold=fonts[1],
        italic=fonts[2],
        boldItalic=fonts[3],
    )


UGENT_BLUE = '#1e64c8'
UGENT_YELLOW = '#ffd200'
ELIS_PURPLE = '#6f71b9'

TEXT_COLOR = '#37474F'  # Blue Grey 800
LIGHT_TEXT_COLOR = '#607D8B'  # Blue Grey 500
DARK_TEXT_COLOR = '#263238'  # Blue Grey 900

PDF_STYLES = {
    'default': ParagraphStyle(
        'default',
        fontName='IBMPlexSans-Regular',
        fontSize=10,
        leading=12,
        textColor=TEXT_COLOR,
    )
}

PDF_STYLES['p'] = ParagraphStyle(
    'p',
    PDF_STYLES['default'],
    spaceBefore=0.35 * cm,
    spaceAfter=0.35 * cm,
)

PDF_STYLES['p_justify'] = ParagraphStyle(
    'p_justify',
    PDF_STYLES['p'],
    alignment=TA_JUSTIFY,
    hyphenationLang='en_GB',
)

PDF_STYLES['p_right'] = ParagraphStyle(
    'p_right',
    PDF_STYLES['p'],
    alignment=TA_RIGHT,
)

PDF_STYLES['p_small'] = ParagraphStyle(
    'p_small',
    PDF_STYLES['p'],
    fontSize=9,
)

PDF_STYLES['footer'] = ParagraphStyle(
    'footer',
    PDF_STYLES['default'],
    fontSize=7,
    leading=9,
    textColor=LIGHT_TEXT_COLOR,
)

PDF_STYLES['ul_li'] = ParagraphStyle(
    'ul_li',
    PDF_STYLES['default'],
    bulletText='•',
    bulletIndent=0.3 * cm,
    leftIndent=0.6 * cm,
    spaceAfter=0.1 * cm,
)

PDF_STYLES['ol_li'] = ParagraphStyle(
    'ol_li',
    PDF_STYLES['ul_li'],
    bulletText='OL',
)

PDF_STYLES['h1'] = ParagraphStyle(
    'h1',
    PDF_STYLES['default'],
    fontName='IBMPlexSans-Light',
    fontSize=23,
    leading=28,
    rightIndent=4 * cm,
    textColor=UGENT_BLUE,
    spaceAfter=0.75 * cm,
)

PDF_STYLES['h2'] = ParagraphStyle(
    'h2',
    PDF_STYLES['default'],
    fontSize=16,
    leading=20,
    rightIndent=4 * cm,
    textColor=UGENT_BLUE,
)

PDF_STYLES['h3'] = ParagraphStyle(
    'h3',
    PDF_STYLES['h2'],
    fontSize=14,
    leading=17,
)

PDF_STYLES['h4'] = ParagraphStyle(
    'h4',
    PDF_STYLES['h2'],
    fontSize=12,
    leading=14,
)

PDF_STYLES['h5'] = ParagraphStyle(
    'h5',
    PDF_STYLES['default'],
    fontSize=12,
    leading=14,
)
