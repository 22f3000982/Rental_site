from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import io

def create_watermark_examples():
    """Create examples of different cursive watermark styles"""
    
    # Different font styles for comparison
    watermark_styles = [
        {
            'name': 'Style 1: Times-Italic (Most Cursive)',
            'main_font': 'Times-Italic',
            'main_size': 70,
            'decoration': '❦',
            'description': 'Most elegant and flowing cursive style'
        },
        {
            'name': 'Style 2: Times-BoldItalic (Bold Cursive)',
            'main_font': 'Times-BoldItalic',
            'main_size': 65,
            'decoration': '✿',
            'description': 'Strong cursive with bold presence'
        },
        {
            'name': 'Style 3: Helvetica-Oblique (Modern Slanted)',
            'main_font': 'Helvetica-Oblique',
            'main_size': 68,
            'decoration': '◊',
            'description': 'Clean modern slanted style'
        },
        {
            'name': 'Style 4: Mixed Style (Times-Italic + Decorations)',
            'main_font': 'Times-Italic',
            'main_size': 72,
            'decoration': '❦',
            'description': 'Enhanced with multiple decorative elements'
        }
    ]
    
    # Create PDF with examples
    c = canvas.Canvas('watermark_cursive_examples.pdf', pagesize=letter)
    width, height = letter
    
    for i, style in enumerate(watermark_styles):
        if i > 0:
            c.showPage()
        
        # Title for each style
        c.setFont("Helvetica-Bold", 16)
        c.drawString(50, height - 50, style['name'])
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 70, style['description'])
        
        # Create watermark example
        c.saveState()
        c.setFillColorRGB(0.8, 0.8, 0.8)
        c.rotate(45)
        
        x_center = (width + height) / 2 - 200
        y_center = (height - width) / 2 + 50
        
        # Add decorative elements
        c.setFont("ZapfDingbats", 12)
        c.drawString(x_center - 140, y_center + 65, style['decoration'])
        
        # Main signature
        c.setFont(style['main_font'], style['main_size'])
        c.drawString(x_center - 130, y_center + 50, "m_@ash")
        
        # Add closing decoration
        c.setFont("ZapfDingbats", 12)
        c.drawString(x_center + 20, y_center + 55, style['decoration'])
        
        if style['name'].startswith('Style 4'):
            # Enhanced decorations for Style 4
            c.setLineWidth(1)
            c.line(x_center - 130, y_center + 45, x_center + 25, y_center + 45)
            
            # Corner decorations
            c.setFont("ZapfDingbats", 10)
            c.drawString(x_center - 150, y_center + 80, "✿")
            c.drawString(x_center + 40, y_center + 80, "✿")
            c.drawString(x_center - 150, y_center + 10, "✿")
            c.drawString(x_center + 40, y_center + 10, "✿")
        
        # Add sample renter name
        c.setFont("Times-Italic", 35)
        c.drawString(x_center - 70, y_center + 5, "✧ SampleRenter ✧")
        
        # Add official text
        c.setFont("Times-Italic", 22)
        c.drawString(x_center - 90, y_center - 35, "• Official Receipt •")
        
        c.restoreState()
        
        # Add sample receipt content
        c.setFont("Helvetica-Bold", 16)
        c.drawString(200, height - 150, "Sample Receipt Content")
        c.setFont("Helvetica", 12)
        c.drawString(50, height - 180, "Receipt ID: SAMPLE-001")
        c.drawString(50, height - 200, "Date: 19-07-2025")
        c.drawString(50, height - 220, "Renter: SampleRenter")
        c.drawString(50, height - 240, "Amount: ₹5000")
        
        # Add border
        c.rect(30, 30, width - 60, height - 60)
    
    c.save()
    print("Watermark examples created: watermark_cursive_examples.pdf")
    
    return watermark_styles

if __name__ == "__main__":
    styles = create_watermark_examples()
    
    print("\n" + "="*60)
    print("CURSIVE WATERMARK STYLE COMPARISON")
    print("="*60)
    
    print("\n🏆 MOST CURSIVE RANKING:")
    print("1. Times-Italic        - Most elegant flowing script")
    print("2. Times-BoldItalic    - Bold cursive with strength")
    print("3. Helvetica-Oblique   - Modern clean slanted")
    print("4. Enhanced Times-Italic - With extra decorations")
    
    print("\n📝 STYLE CHARACTERISTICS:")
    print("• Times-Italic: Classic calligraphy feel, elegant curves")
    print("• Times-BoldItalic: Stronger presence, bold cursive")
    print("• Helvetica-Oblique: Modern, clean, less ornate")
    print("• Enhanced: Times-Italic + decorative flourishes")
    
    print("\n✨ RECOMMENDED: Times-Italic (70pt) for maximum cursive effect")
    print("This provides the most authentic handwritten signature appearance for 'm_@ash'!")
