# Tigo Python API Wrapper

A modern, open-source Python library for interacting with the [Tigo Energy API](https://support.tigoenergy.com/hc/en-us/article_attachments/360041622173). 

## Features

- 🔑 **Automatic authentication** with credentials from environment 
- 📊 **Raw API access** and convenient DataFrame helpers  
- ⚡ **Built-in rate limiting** and error handling
- 🧪 **Well-tested** with comprehensive test suite
- 📈 **Advanced analytics** including system efficiency and panel performance
- 🛡️ **Type hints** for better development experience

## Installation

### From PyPI (when published)
```bash
pip install tigo_python
```

### From GitHub
```bash
pip install git+https://github.com/matt-dreyer/tigo_python.git
```

### Development Installation
```bash
git clone https://github.com/matt-dreyer/tigo_python.git
cd tigo-python
pip install -e ".[dev]"
```

## Quick Start

### 1. Set up credentials

Create a `.env` file in your project root:
```env
TIGO_USERNAME=your_username
TIGO_PASSWORD=your_password
```

Or set environment variables:
```bash
export TIGO_USERNAME=your_username
export TIGO_PASSWORD=your_password
```

### 2. Basic usage

```python
from tigo_python import TigoClient

# Credentials loaded automatically from environment
with TigoClient() as client:
    # Get your systems
    systems = client.list_systems()
    system_id = systems["systems"][0]["system_id"]
    
    # Get current performance
    summary = client.get_summary(system_id)
    print(f"Current power: {summary['summary']['last_power_dc']} W")
    
    # Get historical data as DataFrame
    df = client.get_today_data(system_id)
    print(df.head())
```

### 3. Advanced analytics

```python
# System efficiency analysis
efficiency = client.calculate_system_efficiency(system_id, days_back=30)
print(f"System efficiency: {efficiency['average_efficiency_percent']:.1f}%")

# Panel performance comparison
panel_perf = client.get_panel_performance(system_id)
print(panel_perf.head())

# Find underperforming panels
problems = client.find_underperforming_panels(system_id, threshold_percent=85)
for panel in problems:
    print(f"Panel {panel['panel_id']}: {panel['efficiency_percent']:.1f}% efficiency")
```

## API Coverage

### Core Endpoints
- ✅ **Authentication** - Login/logout with token management
- ✅ **Users** - User information and preferences  
- ✅ **Systems** - List systems, get details and layouts
- ✅ **Sources** - Hardware sources and configurations
- ✅ **Objects** - System components and hierarchy
- ✅ **Data** - Combined and aggregate data endpoints
- ✅ **Alerts** - System alerts and notifications

### Data Formats
- **Raw API responses** - Direct JSON from Tigo API
- **CSV strings** - For integration with other tools
- **Pandas DataFrames** - For data analysis and visualization

## Error Handling

The library provides specific exceptions for different error scenarios:

```python
from tigo_python.exceptions import TigoAPIError, TigoAuthenticationError

try:
    client = TigoClient("wrong_user", "wrong_pass")
except TigoAuthenticationError as e:
    print(f"Login failed: {e}")
except TigoAPIError as e:
    print(f"API error: {e}")
```

## Rate Limiting

The library automatically handles API rate limits by:
- Limiting data requests to safe time ranges (≤20,150 minutes)
- Using appropriate data resolution (minute/hour/day) based on time span
- Providing helpful warnings when requests are adjusted

## Development

### Setup
```bash
git clone https://github.com/matt-dreyer/tigo_python.git
cd tigo-python
pip install -e ".[dev]"
```

### Running Tests
```bash
pytest tests/ -v
```

### Code Quality
```bash
# Linting
ruff check tigo_python/

# Type checking  
mypy tigo_python/

# Formatting
ruff format tigo_python/
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes with tests
4. Ensure code quality checks pass
5. Submit a pull request

## Requirements

- Python ≥ 3.8
- httpx ≥ 0.27.0
- pandas ≥ 2.0.0
- numpy ≥ 1.24.0

## Acknowledgments

This project is inspired by the [Rust tigo client](https://github.com/mrustl/tigo) by [@mrustl](https://github.com/mrustl).

## License

MIT License - see [LICENSE](LICENSE.txt) for details.

---

_This library is not affiliated with or endorsed by Tigo Energy._