# AgentOrchestra Website

This directory contains the GitHub Pages website for the AgentOrchestra project.

## Structure

```
docs/
├── index.html          # Main website page
├── style.css           # Custom CSS styles
├── script.js           # Interactive JavaScript
├── favicon.svg         # Website icon
├── assets/
│   ├── architecture.png # Architecture diagram
│   └── ...            # Other assets
└── README.md           # This file
```

## Features

- **Responsive Design**: Optimized for desktop, tablet, and mobile devices
- **Modern UI**: Built with Tailwind CSS for a clean, professional look
- **Interactive Elements**: Smooth scrolling, animations, and hover effects
- **SEO Optimized**: Proper meta tags and structured content
- **Accessibility**: Focus states and semantic HTML

## Sections

The website follows the paper's structure:

1. **Introduction** - Overview of the project and key principles
2. **Architecture** - System design and component descriptions
3. **Experiments** - Benchmark results and performance metrics
4. **Paper & Resources** - Links to research paper and code repository
5. **Authors** - Team information

## Deployment

The website is automatically deployed to GitHub Pages when changes are pushed to the main branch. The deployment is handled by the GitHub Actions workflow in `.github/workflows/deploy.yml`.

### Manual Deployment

If you need to deploy manually:

1. Ensure all files are in the `docs/` directory
2. Push changes to the main branch
3. GitHub Actions will automatically build and deploy the site

### Local Development

To preview the website locally:

1. Navigate to the `docs/` directory
2. Open `index.html` in a web browser
3. Or use a local server:
   ```bash
   cd docs
   python -m http.server 8000
   # Then visit http://localhost:8000
   ```

## Customization

### Colors
The website uses a custom color palette defined in the Tailwind configuration:
- Primary: Blue shades (#3b82f6, #1d4ed8, etc.)
- Secondary: Gray shades for text and backgrounds

### Animations
Custom CSS animations are defined in `assets/style.css`:
- `fadeIn`: Fade-in effect for sections
- `slideUp`: Slide-up animation for content
- `float`: Floating animation for the architecture diagram

### JavaScript Features
Interactive features in `assets/script.js`:
- Smooth scrolling navigation
- Intersection Observer for scroll animations
- Active navigation highlighting
- Back-to-top button
- Typing animation for the hero title

## Browser Support

The website is compatible with:
- Chrome 90+
- Firefox 88+
- Safari 14+
- Edge 90+

## Performance

The website is optimized for performance:
- Lazy loading for images
- Debounced scroll events
- Optimized CSS and JavaScript
- Minimal external dependencies

## Contributing

To contribute to the website:

1. Make changes to the HTML, CSS, or JavaScript files
2. Test locally to ensure everything works
3. Push changes to trigger automatic deployment
4. The website will be updated at `https://skyworkai.github.io/DeepResearchAgent/`

## License

This website is part of the AgentOrchestra project and follows the same license terms.
