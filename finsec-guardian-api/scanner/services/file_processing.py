import hashlib
from dataclasses import dataclass
from pathlib import Path

from ..compiler import SolidityCompiler

MAX_SOLIDITY_FILE_SIZE = 1_000_000


class FileProcessingError(Exception):
    """Raised when uploaded Solidity input cannot be processed."""


@dataclass
class ProcessedContractSource:
    source_code: str
    contract_name: str
    source_hash: str
    source_type: str
    uploaded_filename: str
    uploaded_file_size: int
    solidity_version: str
    syntax_valid: bool
    syntax_error: str
    compiled_abi: list | None
    compiled_bytecode: str
    compiler_metadata: dict


class SolidityFileProcessingService:
    def process_source_code(self, source_code, contract_name='', solidity_version=''):
        normalized_source = self._normalize_source(source_code)
        return self._build_processed_source(
            source_code=normalized_source,
            contract_name=contract_name,
            solidity_version=solidity_version,
            source_type='text',
            uploaded_filename='',
            uploaded_file_size=len(normalized_source.encode('utf-8')),
        )

    def process_uploaded_file(self, uploaded_file, contract_name='', solidity_version=''):
        filename = getattr(uploaded_file, 'name', '') or 'contract.sol'
        if Path(filename).suffix.lower() != '.sol':
            raise FileProcessingError('Only .sol Solidity files are supported')

        file_size = getattr(uploaded_file, 'size', 0) or 0
        if file_size > MAX_SOLIDITY_FILE_SIZE:
            raise FileProcessingError('Source code exceeds maximum size of 1MB')

        try:
            source_code = uploaded_file.read().decode('utf-8')
        except UnicodeDecodeError as exc:
            raise FileProcessingError('Uploaded Solidity file must be UTF-8 encoded') from exc

        return self._build_processed_source(
            source_code=source_code,
            contract_name=contract_name,
            solidity_version=solidity_version,
            source_type='upload',
            uploaded_filename=filename,
            uploaded_file_size=file_size or len(source_code.encode('utf-8')),
        )

    def _build_processed_source(
        self,
        source_code,
        contract_name,
        solidity_version,
        source_type,
        uploaded_filename,
        uploaded_file_size,
    ):
        normalized_source = self._normalize_source(source_code)
        resolved_version = SolidityCompiler.resolve_solc_version(normalized_source, solidity_version)
        compiler = SolidityCompiler(solc_version=resolved_version)
        compile_result = compiler.compile(normalized_source)
        inferred_name = contract_name.strip() or SolidityCompiler.infer_contract_name(normalized_source)

        compiled_abi = None
        compiled_bytecode = ''
        syntax_error = ''
        compiler_metadata = {'compiler_version': resolved_version}

        if compile_result['success']:
            selected_name, contract_data = SolidityCompiler.extract_primary_contract(
                compile_result['data'],
                inferred_name,
            )
            inferred_name = selected_name
            if contract_data:
                compiled_abi = contract_data.get('abi', [])
                compiled_bytecode = contract_data.get('bin', '')
                compiler_metadata['contract_keys'] = list(compile_result['data'].keys())
        else:
            syntax_error = compile_result['error'] or 'Solidity compilation failed'

        return ProcessedContractSource(
            source_code=normalized_source,
            contract_name=inferred_name,
            source_hash=hashlib.sha256(normalized_source.encode('utf-8')).hexdigest(),
            source_type=source_type,
            uploaded_filename=uploaded_filename,
            uploaded_file_size=uploaded_file_size,
            solidity_version=resolved_version,
            syntax_valid=compile_result['success'],
            syntax_error=syntax_error,
            compiled_abi=compiled_abi,
            compiled_bytecode=compiled_bytecode,
            compiler_metadata=compiler_metadata,
        )

    @staticmethod
    def _normalize_source(source_code):
        if not source_code or len(source_code.strip()) == 0:
            raise FileProcessingError('Source code cannot be empty')

        if len(source_code.encode('utf-8')) > MAX_SOLIDITY_FILE_SIZE:
            raise FileProcessingError('Source code exceeds maximum size of 1MB')

        return source_code.strip() + '\n'