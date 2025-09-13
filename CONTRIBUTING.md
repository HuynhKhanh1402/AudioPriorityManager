# Contributing to Audio Priority Manager

Thank you for your interest in contributing to Audio Priority Manager! This document provides guidelines for contributing to the project.

## 🤝 How to Contribute

### Reporting Bugs
1. Check if the bug has already been reported in the Issues section
2. Create a new issue with:
   - Clear description of the problem
   - Steps to reproduce
   - Expected vs actual behavior
   - System information (Windows version, Python version)
   - Log files if applicable

### Suggesting Features
1. Check existing feature requests
2. Create a new issue with:
   - Clear description of the feature
   - Use case and benefits
   - Possible implementation approach

### Code Contributions

#### Setting up Development Environment
```bash
# Clone the repository
git clone <repository-url>
cd AudioPriority

# Create virtual environment
python -m venv .venv
.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies
pip install pytest black flake8 mypy
```

#### Code Style
- Follow PEP 8 style guidelines
- Use `black` for code formatting: `black src/`
- Use `flake8` for linting: `flake8 src/`
- Use type hints where appropriate

#### Testing
- Add tests for new features
- Ensure existing tests pass: `pytest`
- Test on different Windows versions if possible

#### Pull Request Process
1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Add/update tests
5. Update documentation if needed
6. Commit with clear messages
7. Push to your fork
8. Create a Pull Request

#### Commit Messages
Use clear, descriptive commit messages:
```
feat: add real-time audio level display
fix: resolve volume restoration issue
docs: update installation instructions
refactor: improve audio engine performance
```

## 📋 Development Guidelines

### Architecture
- Keep GUI (`gui.py`) and audio logic (`audio_engine.py`) separate
- Use dependency injection for testing
- Handle errors gracefully with user-friendly messages

### Audio Engine
- Respect Windows audio session management
- Always restore original volumes on exit
- Use appropriate COM threading models

### GUI
- Follow PyQt6 best practices
- Provide tooltips for all controls
- Use keyboard shortcuts consistently
- Ensure accessibility

### Performance
- Minimize CPU usage in audio monitoring loop
- Use appropriate polling intervals
- Avoid blocking the GUI thread

## 🐛 Debugging

### Common Issues
- Audio API permissions
- COM threading issues
- Process name matching
- Volume restoration failures

### Debug Tools
- Enable verbose logging
- Use Windows Audio troubleshooter
- Monitor with Process Monitor
- Check Windows Event Viewer

## 📝 Documentation

### Code Documentation
- Use docstrings for all public methods
- Include type hints
- Document complex algorithms
- Provide usage examples

### User Documentation
- Update README for new features
- Keep QUICKSTART.txt current
- Add tooltips for GUI elements
- Create help documentation

## 🔍 Review Process

All contributions will be reviewed for:
- Code quality and style
- Functionality and testing
- Documentation completeness
- Performance impact
- Security considerations

## 📞 Getting Help

- Open an issue for questions
- Check existing documentation
- Review similar audio applications
- Ask in discussions section

Thank you for contributing! 🎉
