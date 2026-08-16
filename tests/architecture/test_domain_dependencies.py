import ast
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parents[2]
SOURCE_ROOT = PROJECT_ROOT / "src" / "noema"
PROHIBITED_IMPORTS = frozenset(
    {
        "anthropic",
        "autogen",
        "crewai",
        "fastapi",
        "httpx",
        "langchain",
        "langgraph",
        "openai",
        "pydantic",
        "qdrant_client",
        "requests",
        "sqlalchemy",
    }
)


def imported_modules(path: Path) -> list[tuple[str, int]]:
    """Return imported module names and their source lines."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    imports: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.extend((alias.name, node.lineno) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.append((node.module, node.lineno))
    return imports


def prohibited_domain_imports(source_root: Path) -> list[str]:
    """Return prohibited imports found below any domain package."""
    violations: list[str] = []
    for path in sorted(source_root.glob("**/domain/**/*.py")):
        for module, line_number in imported_modules(path):
            root_module = module.split(".", maxsplit=1)[0]
            if root_module in PROHIBITED_IMPORTS:
                relative_path = path.relative_to(source_root)
                violations.append(f"{relative_path}:{line_number} imports {module}")
    return violations


def test_domain_has_no_prohibited_dependencies() -> None:
    assert prohibited_domain_imports(SOURCE_ROOT) == []


def test_shared_domain_does_not_import_cognition() -> None:
    shared_domain = SOURCE_ROOT / "shared" / "domain"
    violations = [
        str(path.relative_to(SOURCE_ROOT))
        for path in sorted(shared_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module == "noema.cognition" or module.startswith("noema.cognition.")
    ]

    assert violations == []


@pytest.mark.parametrize("statement", ["import fastapi", "from sqlalchemy.orm import Session"])
def test_scanner_detects_prohibited_imports(tmp_path: Path, statement: str) -> None:
    domain = tmp_path / "example" / "domain"
    domain.mkdir(parents=True)
    (domain / "model.py").write_text(statement, encoding="utf-8")

    violations = prohibited_domain_imports(tmp_path)

    assert len(violations) == 1


def test_workspace_has_only_allowed_noema_dependencies() -> None:
    workspace_domain = SOURCE_ROOT / "cognition" / "domain" / "workspace"
    allowed_prefixes = (
        "noema.cognition.domain.errors",
        "noema.cognition.domain.workspace",
        "noema.shared.domain",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(workspace_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_attention_has_only_allowed_noema_dependencies() -> None:
    attention_domain = SOURCE_ROOT / "cognition" / "domain" / "attention"
    allowed_prefixes = (
        "noema.cognition.domain.attention",
        "noema.cognition.domain.errors",
        "noema.shared.domain",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(attention_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_situation_has_only_allowed_noema_dependencies() -> None:
    situation_domain = SOURCE_ROOT / "cognition" / "domain" / "situation"
    allowed_prefixes = (
        "noema.cognition.domain.errors",
        "noema.cognition.domain.situation",
        "noema.shared.domain",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(situation_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_epistemology_has_only_allowed_noema_dependencies() -> None:
    epistemology_domain = SOURCE_ROOT / "cognition" / "domain" / "epistemology"
    allowed_prefixes = (
        "noema.cognition.domain.epistemology",
        "noema.cognition.domain.errors",
        "noema.shared.domain",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(epistemology_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_budget_has_only_allowed_noema_dependencies() -> None:
    budget_domain = SOURCE_ROOT / "cognition" / "domain" / "budget"
    allowed_prefixes = (
        "noema.cognition.domain.budget",
        "noema.cognition.domain.errors",
        "noema.shared.domain",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(budget_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_modes_has_only_allowed_noema_dependencies() -> None:
    modes_domain = SOURCE_ROOT / "cognition" / "domain" / "modes"
    allowed_prefixes = (
        "noema.cognition.domain.errors",
        "noema.cognition.domain.modes",
        "noema.shared.domain",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(modes_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_mode_arbitration_has_only_allowed_noema_dependencies() -> None:
    arbitration_domain = SOURCE_ROOT / "cognition" / "domain" / "mode_arbitration"
    allowed_prefixes = (
        "noema.cognition.domain.errors",
        "noema.cognition.domain.mode_arbitration",
        "noema.cognition.domain.modes",
        "noema.shared.domain",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(arbitration_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_context_composition_has_only_allowed_noema_dependencies() -> None:
    composition_domain = SOURCE_ROOT / "cognition" / "domain" / "context_composition"
    allowed_prefixes = (
        "noema.cognition.domain.context",
        "noema.cognition.domain.context_composition",
        "noema.cognition.domain.errors",
        "noema.cognition.domain.modes",
        "noema.shared.domain",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(composition_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_context_and_modes_do_not_import_context_composition() -> None:
    protected_domains = (
        SOURCE_ROOT / "cognition" / "domain" / "context",
        SOURCE_ROOT / "cognition" / "domain" / "modes",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for domain in protected_domains
        for path in sorted(domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module == "noema.cognition.domain.context_composition"
        or module.startswith("noema.cognition.domain.context_composition.")
    ]

    assert violations == []


def test_reasoning_has_only_allowed_noema_dependencies() -> None:
    reasoning_domain = SOURCE_ROOT / "cognition" / "domain" / "reasoning"
    allowed_prefixes = (
        "noema.cognition.domain.budget",
        "noema.cognition.domain.context_composition",
        "noema.cognition.domain.errors",
        "noema.cognition.domain.reasoning",
        "noema.shared.domain",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(reasoning_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_cognition_domain_does_not_import_cognition_ports() -> None:
    cognition_domain = SOURCE_ROOT / "cognition" / "domain"
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(cognition_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module == "noema.cognition.ports" or module.startswith("noema.cognition.ports.")
    ]

    assert violations == []


def test_cognition_ports_has_only_allowed_noema_dependencies() -> None:
    ports_domain = SOURCE_ROOT / "cognition" / "ports"
    allowed_prefixes = (
        "noema.cognition.domain.reasoning",
        "noema.cognition.ports",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(ports_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_cognition_ports_has_no_prohibited_dependencies() -> None:
    ports_domain = SOURCE_ROOT / "cognition" / "ports"
    violations = [
        f"{path.relative_to(SOURCE_ROOT)}:{line_number} imports {module}"
        for path in sorted(ports_domain.glob("**/*.py"))
        for module, line_number in imported_modules(path)
        if module.split(".", maxsplit=1)[0] in PROHIBITED_IMPORTS
    ]

    assert violations == []


def test_cognition_domain_does_not_import_cognition_application() -> None:
    cognition_domain = SOURCE_ROOT / "cognition" / "domain"
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(cognition_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module == "noema.cognition.application"
        or module.startswith("noema.cognition.application.")
    ]

    assert violations == []


def test_cognition_application_has_only_allowed_noema_dependencies() -> None:
    application_domain = SOURCE_ROOT / "cognition" / "application"
    allowed_prefixes = (
        "noema.cognition.application",
        "noema.cognition.domain.reasoning",
        "noema.cognition.ports",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(application_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_cognition_application_has_no_prohibited_dependencies() -> None:
    application_domain = SOURCE_ROOT / "cognition" / "application"
    violations = [
        f"{path.relative_to(SOURCE_ROOT)}:{line_number} imports {module}"
        for path in sorted(application_domain.glob("**/*.py"))
        for module, line_number in imported_modules(path)
        if module.split(".", maxsplit=1)[0] in PROHIBITED_IMPORTS
    ]

    assert violations == []


def test_model_router_domain_has_only_allowed_noema_dependencies() -> None:
    model_router_domain = SOURCE_ROOT / "model_router" / "domain"
    allowed_prefixes = (
        "noema.model_router.domain",
        "noema.shared.domain",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(model_router_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_model_router_application_has_only_allowed_noema_dependencies() -> None:
    application_domain = SOURCE_ROOT / "model_router" / "application"
    allowed_prefixes = (
        "noema.model_router.application",
        "noema.model_router.domain",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(application_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_model_router_application_has_no_prohibited_dependencies() -> None:
    application_domain = SOURCE_ROOT / "model_router" / "application"
    violations = [
        f"{path.relative_to(SOURCE_ROOT)}:{line_number} imports {module}"
        for path in sorted(application_domain.glob("**/*.py"))
        for module, line_number in imported_modules(path)
        if module.split(".", maxsplit=1)[0] in PROHIBITED_IMPORTS
    ]

    assert violations == []


def test_model_router_ports_has_only_allowed_noema_dependencies() -> None:
    ports_domain = SOURCE_ROOT / "model_router" / "ports"
    allowed_prefixes = (
        "noema.model_router.ports",
        "noema.model_router.domain",
    )
    violations = [
        f"{path.relative_to(SOURCE_ROOT)} imports {module}"
        for path in sorted(ports_domain.glob("**/*.py"))
        for module, _ in imported_modules(path)
        if module.startswith("noema.")
        and not any(
            module == prefix or module.startswith(f"{prefix}.") for prefix in allowed_prefixes
        )
    ]

    assert violations == []


def test_model_router_ports_has_no_prohibited_dependencies() -> None:
    ports_domain = SOURCE_ROOT / "model_router" / "ports"
    violations = [
        f"{path.relative_to(SOURCE_ROOT)}:{line_number} imports {module}"
        for path in sorted(ports_domain.glob("**/*.py"))
        for module, line_number in imported_modules(path)
        if module.split(".", maxsplit=1)[0] in PROHIBITED_IMPORTS
    ]

    assert violations == []
