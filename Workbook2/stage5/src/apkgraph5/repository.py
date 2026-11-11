"""Индексация пакетов и разрешение прямых и виртуальных зависимостей."""

from .models import AppError
from .versions import satisfies, split_dependency, version_key


class Repository:
    """Пакеты одного репозитория с поиском по имени и provides."""

    def __init__(self, packages):
        """Построить индексы имен и виртуальных поставщиков пакетов."""
        self.packages = sorted(packages)
        self.names = {}
        self.providers = {}
        for package in self.packages:
            self.add_package(package)

    def add_package(self, package):
        """Добавить пакет, отклонив повтор его имени и версии."""
        existing = self.names.get(package.name, [])
        if any(item.version == package.version for item in existing):
            raise AppError(f"Повтор пакета: {package.key}")
        self.names.setdefault(package.name, []).append(package)
        for provide in package.provides:
            name, operator, version = split_dependency(provide)
            entry = package, version if operator else ""
            self.providers.setdefault(name, []).append(entry)

    def root(self, name, version):
        """Найти корневой пакет с точно указанной пользователем версией."""
        for package in self.names.get(name, []):
            if package.version == version:
                return package
        raise AppError(f"Пакет {name} версии {version} не найден")

    def virtual_candidates(self, name, operator, wanted):
        """Найти поставщиков виртуального имени с подходящей версией."""
        result = []
        for package, provided in self.providers.get(name, []):
            if not operator or (
                provided and satisfies(provided, operator, wanted)
            ):
                result.append(package)
        return result

    def resolve(self, dependency):
        """Выбрать пакет, удовлетворяющий одной прямой зависимости."""
        name, operator, wanted = split_dependency(dependency)
        candidates = [
            package
            for package in self.names.get(name, [])
            if satisfies(package.version, operator, wanted)
        ]
        if not candidates:
            candidates = self.virtual_candidates(name, operator, wanted)
        if not candidates:
            raise AppError(
                f"Зависимость {dependency} отсутствует в выбранном репозитории"
            )
        return max(candidates, key=package_order)

    def dependencies(self, package, excluded=""):
        """Получить прямые зависимости, применив фильтр к обоим именам."""
        result = []
        for dependency in package.dependencies:
            if dependency.startswith("!"):
                continue
            name, _, _ = split_dependency(dependency)
            if excluded and excluded in name:
                continue
            target = self.resolve(dependency)
            if not excluded or excluded not in target.name:
                result.append(target)
        return sorted(set(result))


def package_order(package):
    """Получить детерминированный ключ выбора версии и поставщика."""
    return version_key(package.version), package.name
