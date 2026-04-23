from solcx import compile_source, set_solc_version, install_solc
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class SolidityCompiler:
    def __init__(self, solc_version='0.8.21'):
        self.solc_version = solc_version
        try:
            set_solc_version(self.solc_version)
        except:
            install_solc(self.solc_version)
            set_solc_version(self.solc_version)
    
    def compile(self, source_code):
        """Compile Solidity source code and return artifacts"""
        try:
            compiled = compile_source(source_code)
            return {
                'success': True,
                'data': compiled,
                'error': None
            }
        except Exception as e:
            logger.error(f"Compilation error: {str(e)}")
            return {
                'success': False,
                'data': None,
                'error': str(e)
            }
    
    def extract_contract_info(self, compiled_dict, contract_name):
        """Extract ABI, bytecode, and metadata"""
        contract_key = f'<stdin>:{contract_name}'
        if contract_key not in compiled_dict:
            return None
        
        contract = compiled_dict[contract_key]
        return {
            'abi': contract.get('abi', []),
            'bytecode': contract.get('bin', ''),
            'metadata': contract.get('metadata', {}),
        }