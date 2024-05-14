import re


class ServiceLint:
    def __init__(self):
        self.required_service_fields = ['id', 'name', 'microservices']
        self.required_ms_fields = ['id', 'name', 'url', 'active']

    def is_valid_url(self, url):
        """Проверяет URL на соответствие начальным http:// или https://."""
        return re.match(r'https?://', url) is not None

    def has_required_fields(self, data, required_fields):
        """Проверяет наличие всех требуемых полей."""
        return [field for field in required_fields if field not in data]

    def lint_services(self, services):
        """Осуществляет проверку списка услуг на соответствие требованиям."""
        errors = []
        for service in services:
            missing_service_fields = self.has_required_fields(service, self.required_service_fields)
            if missing_service_fields:
                errors.append(
                    f"Service {service.get('id', 'Unknown')} is missing fields: {', '.join(missing_service_fields)}")
            for ms in service.get('microservices', []):
                missing_ms_fields = self.has_required_fields(ms, self.required_ms_fields)
                if missing_ms_fields:
                    errors.append(
                        f"Microservice {ms.get('id', 'Unknown')} in Service {service['id']} is missing fields: {', '.join(missing_ms_fields)}")
                if not self.is_valid_url(ms['url']):
                    errors.append(f"Microservice {ms['id']} in Service {service['id']} has invalid URL: {ms['url']}")
        return errors
