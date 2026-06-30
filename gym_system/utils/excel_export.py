from services.export_service import ExportService

def get_clients_excel(clients):
    return ExportService.export_clients_excel(clients)

def get_payments_excel(payments):
    return ExportService.export_payments_excel(payments)
