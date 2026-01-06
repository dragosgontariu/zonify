"""
Dependency Checker for Zonify

Checks if required Python packages are installed.
Provides detailed information and installation commands.
Allows graceful degradation (skip features if deps missing).

Author: Dragos Gontariu
License: GPL-3.0
"""

import sys
from typing import List, Dict, Tuple


class DependencyChecker:
    """
    Check if required Python packages are installed.
    Provides detailed feedback and installation instructions.
    """
    
    # Core packages (absolutely required)
    CORE_PACKAGES = {
        'numpy': '1.24.0',
        'scipy': '1.11.0',
    }
    
    # Feature-specific packages (optional, enable specific features)
    FEATURE_PACKAGES = {
        'pandas': {
            'version': '2.0.0',
            'features': ['CSV export', 'data processing']
        },
        'reportlab': {
            'version': '4.0.0',
            'features': ['PDF export']
        },
        'jinja2': {
            'version': '3.1.0',
            'features': ['HTML export']
        },
        'plotly': {
            'version': '5.18.0',
            'features': ['Interactive charts']
        },
        'matplotlib': {
            'version': '3.8.0',
            'features': ['Static charts']
        },
    }
    
    def check_dependencies(self) -> Tuple[List[str], List[str], Dict[str, List[str]]]:
        """
        Check if all required packages are installed.
        
        Returns:
            Tuple: (missing_core, missing_features, available_features)
                - missing_core: List of missing core package names
                - missing_features: List of missing feature package names
                - available_features: Dict of package -> features that will work
        """
        missing_core = []
        missing_features = []
        available_features = {}
        
        # Check core packages
        for package, min_version in self.CORE_PACKAGES.items():
            if not self._is_package_installed(package):
                missing_core.append(package)
        
        # Check feature packages
        for package, info in self.FEATURE_PACKAGES.items():
            if self._is_package_installed(package):
                available_features[package] = info['features']
            else:
                missing_features.append(package)
        
        return missing_core, missing_features, available_features
    
    def get_detailed_report(self) -> Dict:
        """
        Get detailed dependency report.
        
        Returns:
            Dict: Detailed report with installation status
        """
        missing_core, missing_features, available_features = self.check_dependencies()
        
        report = {
            'all_ok': len(missing_core) == 0,
            'can_run': len(missing_core) == 0,
            'missing_core': missing_core,
            'missing_features': missing_features,
            'available_features': available_features,
            'disabled_features': self._get_disabled_features(missing_features)
        }
        
        return report
    
    def _get_disabled_features(self, missing_packages: List[str]) -> List[str]:
        """Get list of features that will be disabled."""
        disabled = []
        for package in missing_packages:
            if package in self.FEATURE_PACKAGES:
                disabled.extend(self.FEATURE_PACKAGES[package]['features'])
        return disabled
    
    def _is_package_installed(self, package_name: str) -> bool:
        """
        Check if a single package is installed.
        
        Args:
            package_name (str): Name of the package to check
            
        Returns:
            bool: True if installed, False otherwise
        """
        try:
            __import__(package_name)
            return True
        except ImportError:
            return False
    
    def get_installation_command(self, packages: List[str]) -> str:
        """
        Generate installation command for missing packages.
        
        Args:
            packages (List[str]): List of missing package names
            
        Returns:
            str: Installation command
        """
        if not packages:
            return ''
        
        return f'python -m pip install {" ".join(packages)}'
    
    def get_installation_instructions(self, missing_core: List[str], missing_features: List[str]) -> str:
        """
        Get detailed installation instructions.
        
        Args:
            missing_core (List[str]): Missing core packages
            missing_features (List[str]): Missing feature packages
            
        Returns:
            str: Detailed installation instructions
        """
        instructions = []
        
        if missing_core:
            instructions.append("CRITICAL - Core packages missing (plugin won't work):")
            instructions.append(f"  {', '.join(missing_core)}")
            instructions.append(f"\nInstall with:")
            instructions.append(f"  python -m pip install {' '.join(missing_core)}")
            instructions.append("")
        
        if missing_features:
            instructions.append("OPTIONAL - Feature packages missing (some exports disabled):")
            for package in missing_features:
                features = self.FEATURE_PACKAGES[package]['features']
                instructions.append(f"  • {package}: enables {', '.join(features)}")
            instructions.append(f"\nInstall all optional packages:")
            instructions.append(f"  python -m pip install {' '.join(missing_features)}")
            instructions.append(f"\nOr install individually as needed.")
        
        return '\n'.join(instructions)