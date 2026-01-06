# Contributing to Zonify

First off, thank you for considering contributing to Zonify! It's people like you that make Zonify such a great tool.

## Code of Conduct

By participating in this project, you are expected to uphold our Code of Conduct:
- Be respectful and inclusive
- Welcome newcomers
- Focus on what is best for the community
- Show empathy towards other community members

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the existing issues to avoid duplicates. When you create a bug report, include as many details as possible:

**Bug Report Template:**
```markdown
**Describe the bug**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '...'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g. Windows 10, Ubuntu 22.04]
 - QGIS Version: [e.g. 3.28.2]
 - Zonify Version: [e.g. 1.0.0]
 - Python Version: [e.g. 3.9.5]

**Additional context**
Any other context about the problem.
```

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, include:

**Enhancement Template:**
```markdown
**Is your feature request related to a problem?**
A clear description of what the problem is.

**Describe the solution you'd like**
A clear description of what you want to happen.

**Describe alternatives you've considered**
Any alternative solutions or features you've considered.

**Additional context**
Any other context or screenshots about the feature request.
```

### Your First Code Contribution

Unsure where to begin? Look for issues tagged with:
- `good first issue` - Simple issues for newcomers
- `help wanted` - Issues where we need community help

### Pull Requests

1. **Fork the repo** and create your branch from `main`
2. **Follow the code style:**
   - Use 4 spaces for indentation (not tabs)
   - Follow PEP 8 style guide
   - Add docstrings to all functions/classes
   - Keep lines under 100 characters where possible
3. **Test your changes:**
   - Ensure existing functionality still works
   - Add unit tests for new features
   - Test on at least one operating system
4. **Update documentation:**
   - Update README if needed
   - Update CHANGELOG.md
   - Add docstrings to new code
5. **Commit your changes:**
   - Use clear commit messages
   - Reference issues in commits (e.g., "Fixes #123")
6. **Push to your fork** and submit a pull request

**Pull Request Template:**
```markdown
**Description**
Brief description of what this PR does.

**Related Issue**
Fixes #(issue number)

**Type of Change**
- [ ] Bug fix (non-breaking change)
- [ ] New feature (non-breaking change)
- [ ] Breaking change (fix or feature that breaks existing functionality)
- [ ] Documentation update

**Testing**
- [ ] I have tested this code locally
- [ ] I have added/updated unit tests
- [ ] All tests pass
- [ ] I have updated documentation

**Screenshots (if applicable)**
Add screenshots to demonstrate the change.

**Checklist**
- [ ] My code follows the project's style guidelines
- [ ] I have performed a self-review of my code
- [ ] I have commented my code where necessary
- [ ] I have updated the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix/feature works
```

## Development Setup

### Prerequisites
- QGIS 3.28+
- Python 3.9+
- Git

### Setup Steps

1. **Clone the repository:**
   ```bash
   git clone https://github.com/dragosgontariu/zonify.git
   cd zonify
   ```

2. **Create symbolic link to QGIS plugins directory:**
   
   **Windows:**
   ```bash
   mklink /D "C:\Users\<username>\AppData\Roaming\QGIS\QGIS3\profiles\default\python\plugins\Zonify" "C:\path\to\zonify"
   ```
   
   **Linux/Mac:**
   ```bash
   ln -s /path/to/zonify ~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/Zonify
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Reload plugin in QGIS:**
   - Use Plugin Reloader plugin for quick testing
   - Or restart QGIS after each change

### Running Tests

```bash
# Install pytest
pip install pytest pytest-cov

# Run all tests
pytest

# Run with coverage
pytest --cov=Zonify tests/

# Run specific test file
pytest tests/test_processor.py
```

### Code Style

We use:
- **PEP 8** for Python code style
- **Black** for code formatting (optional but recommended)
- **pylint** for linting

```bash
# Format code with Black
black zonify/

# Check with pylint
pylint zonify/
```

## Project Structure

```
Zonify/
├── algorithms/          # Processing algorithms
│   ├── advanced_stats.py
│   ├── custom_algorithm_engine.py
│   ├── post_processing_engine.py
│   └── time_series_engine.py
├── core/               # Core processing logic
│   ├── processor.py
│   └── zonal_calculator.py
├── export/             # Export formats
│   ├── csv_exporter.py
│   ├── html_exporter.py
│   ├── json_exporter.py
│   └── pdf_exporter.py
├── ui/                 # User interface
│   ├── widgets/
│   │   ├── score_creator_widget.py
│   │   ├── area_classifier_widget.py
│   │   └── ... (other widgets)
│   ├── main_dialog.py
│   └── progress_dialog.py
├── utils/              # Utilities
│   ├── dependency_checker.py
│   ├── logger.py
│   └── progress_tracker.py
├── tests/              # Unit tests
├── docs/               # Documentation
├── examples/           # Example data
├── metadata.txt        # QGIS plugin metadata
├── requirements.txt    # Python dependencies
└── README.md
```

## Documentation

When adding new features:
- Add docstrings to all functions/classes
- Update user documentation in `docs/`
- Add examples if applicable
- Update CHANGELOG.md

**Docstring Format:**
```python
def function_name(arg1, arg2):
    """
    Brief description.
    
    Longer description if needed.
    
    Args:
        arg1 (type): Description
        arg2 (type): Description
    
    Returns:
        type: Description
    
    Raises:
        ExceptionType: When this happens
    """
    pass
```

## Commit Message Guidelines

- Use present tense ("Add feature" not "Added feature")
- Use imperative mood ("Move cursor to..." not "Moves cursor to...")
- Limit first line to 72 characters
- Reference issues and pull requests after first line

**Examples:**
```
Add support for 3D rasters

Fixes #123

- Implement Z-dimension handling
- Update tests
- Add documentation
```

## Release Process

1. Update version in `metadata.txt`
2. Update CHANGELOG.md
3. Create git tag: `git tag v1.0.0`
4. Push tag: `git push origin v1.0.0`
5. Create GitHub release with notes
6. Package plugin and upload to QGIS repository

## Questions?

- Open an issue with the `question` label
- Start a discussion on GitHub Discussions
- Email: gontariudragos@gmail.com

## License

By contributing, you agree that your contributions will be licensed under the GPL-3.0 License.

---

Thank you for contributing to Zonify! 🎉
