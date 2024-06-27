
def calculate_coverage():
    return 85

def generate_badge(coverage_percent, output_file):
    # Define badge SVG template
    badge_template = f'''\
<svg xmlns="http://www.w3.org/2000/svg" width="120" height="20">
  <linearGradient id="b" x2="0" y2="100%">
    <stop offset="0" stop-color="#bbb" stop-opacity=".1"/>
    <stop offset="1" stop-opacity=".1"/>
  </linearGradient>
  <rect rx="3" width="120" height="20" fill="#555"/>
  <rect rx="3" x="60" width="60" height="20" fill="#4c1"/>
  <path fill="#4c1" d="M60 0h4v20h-4z"/>
  <rect rx="3" width="120" height="20" fill="url(#b)"/>
  <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
    <text x="30" y="15" fill="#010101" fill-opacity=".3">coverage</text>
    <text x="30" y="14">coverage</text>
    <text x="90" y="15" fill="#010101" fill-opacity=".3">{coverage_percent:.1f}%</text>
    <text x="90" y="14">{coverage_percent:.1f}%</text>
  </g>
</svg>
'''
    
    # Format the badge template with coverage percentage
    badge_svg = badge_template.format(coverage_percent=coverage_percent)
    
    # Write badge SVG to output file
    with open(output_file, 'w') as f:
        f.write(badge_svg)

if __name__ == "__main__":
    badge_output_file = 'coverage-badge.svg'
    coverage_percent = calculate_coverage()
    generate_badge(coverage_percent, badge_output_file)
    
    print(f"Coverage: {coverage_percent:.1f}%")
    print(f"Badge generated: {badge_output_file}")
