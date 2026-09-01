# Contributing to S214 Sales Platform

Thank you for your interest in contributing to this project! We welcome contributions from the community.

## How to Contribute

### Reporting Issues

- Use the GitHub issue tracker
- Describe the issue clearly
- Include steps to reproduce
- Specify expected vs actual behavior

### Submitting Pull Requests

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes
4. Run tests (`./scripts/test.sh`)
5. Run validation (`./scripts/validate.sh`)
6. Commit your changes (`git commit -m 'Add your feature'`)
7. Push to the branch (`git push origin feature/your-feature`)
8. Open a Pull Request

## Development Setup

```bash
# Clone the repository
git clone https://github.com/username/s214-sales-platform.git
cd s214-sales-platform

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r src/processor/requirements.txt
pip install -r tests/requirements.txt
```

## Code Style

- Follow PEP 8 guidelines
- Use meaningful variable names
- Write docstrings for functions
- Keep functions focused and small

## Testing

- Write unit tests for new features
- Ensure all tests pass before submitting
- Aim for good code coverage

## Code Review

All submissions require review before being merged. We appreciate your patience.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.