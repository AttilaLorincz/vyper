from vyper.exceptions import StructureException
from vyper.compiler import (
    compile_codes,
    compile_code
)
from vyper.signatures.interface import (
    extract_file_interface_imports,
    extract_sigs,
)
from vyper.interfaces import ERC20, ERC721


def test_basic_extract_interface():
    code = """
# Events

Transfer: event({_from: address, _to: address, _value: uint256})

# Functions

@constant
@public
def allowance(_owner: address, _spender: address) -> (uint256, uint256):
    return 1, 2
    """

    out = compile_code(code, ['interface'])
    out = out['interface']
    code_pass = '\n'.join(code.split('\n')[:-2] + ['    pass'])  # replace with a pass statement.

    assert code_pass.strip() == out.strip()


def test_basic_extract_external_interface():
    code = """
@constant
@public
def allowance(_owner: address, _spender: address) -> (uint256, uint256):
    return 1, 2

@public
def test(_owner: address):
    pass

@constant
@private
def _prive(_owner: address, _spender: address) -> (uint256, uint256):
    return 1, 2
    """

    interface = """
# External Contracts
contract One:
    def allowance(_owner: address, _spender: address) -> (uint256, uint256): constant
    def test(_owner: address): modifying
    """

    out = compile_codes({'one.vy': code}, ['external_interface'])[0]
    out = out['external_interface']

    assert interface.strip() == out.strip()


def test_basic_interface_implements(assert_compile_failed):
    code = """
from vyper.interfaces import ERC20

implements: ERC20


@public
def test() -> bool:
    return True
    """

    assert_compile_failed(
        lambda: compile_codes({'one.vy': code}),
        StructureException
    )


def test_builtin_interfaces_parse():
    assert len(extract_sigs(ERC20.interface_code)) == 8
    assert len(extract_sigs(ERC721.interface_code)) == 13


def test_external_interface_parsing(assert_compile_failed):
    interface_code = """
@public
def foo() -> uint256:
    pass

@public
def bar() -> uint256:
    pass
    """

    interface_codes = {
        'FooBarInterface': interface_code
    }

    code = """
import a as FooBarInterface

implements: FooBarInterface

@public
def foo() -> uint256:
    return 1

@public
def bar() -> uint256:
    return 2
    """

    assert compile_codes({'one.vy': code}, interface_codes=interface_codes)[0]

    not_implemented_code = """
import a as FooBarInterface

implements: FooBarInterface

@public
def foo() -> uint256:
    return 1

    """

    assert_compile_failed(
        lambda: compile_codes({'one.vy': not_implemented_code}, interface_codes=interface_codes)[0],
        StructureException
    )


def test_extract_file_interface_imports(assert_compile_failed):
    code = """
import a as FooBarInterface
    """

    assert extract_file_interface_imports(code) == {'FooBarInterface': 'a'}

    invalid_no_alias_code = """
import a
    """
    assert_compile_failed(
        lambda: extract_file_interface_imports(invalid_no_alias_code), StructureException
    )

    invalid_interfac_already_exists_code = """
import a as A
import a as A
    """
    assert_compile_failed(lambda: extract_file_interface_imports(invalid_interfac_already_exists_code), StructureException)  # noqa: E501
