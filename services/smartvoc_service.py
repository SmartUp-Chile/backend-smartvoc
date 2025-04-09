import logging
from datetime import datetime
from app import db
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import text, inspect
from exceptions.custom_exceptions import ResourceNotFoundError, ValidationError

logger = logging.getLogger(__name__)

class SmartVOCService:
    def __init__(self):
        self.table_name = 'smartvoc_clients'
    
    def _ensure_table_exists(self):
        """Asegura que la tabla de clientes existe en la base de datos"""
        try:
            inspector = inspect(db.engine)
            if not inspector.has_table(self.table_name):
                logger.info(f"Creando tabla {self.table_name}...")
                query = text(f"""
                CREATE TABLE IF NOT EXISTS {self.table_name} (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL UNIQUE,
                    api_key VARCHAR(100) NOT NULL UNIQUE,
                    config JSONB DEFAULT '{}',
                    active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """)
                db.session.execute(query)
                db.session.commit()
                logger.info(f"Tabla {self.table_name} creada correctamente")
            return True
        except SQLAlchemyError as e:
            logger.error(f"Error al verificar/crear tabla {self.table_name}: {str(e)}")
            db.session.rollback()
            raise
    
    def get_clients(self):
        """Obtiene todos los clientes registrados"""
        self._ensure_table_exists()
        try:
            query = text(f"SELECT * FROM {self.table_name} ORDER BY name")
            result = db.session.execute(query)
            clients = []
            for row in result:
                client = {
                    'id': row.id,
                    'name': row.name,
                    'api_key': row.api_key,
                    'config': row.config,
                    'active': row.active,
                    'created_at': row.created_at,
                    'updated_at': row.updated_at
                }
                clients.append(client)
            return clients
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener clientes: {str(e)}")
            raise ResourceNotFoundError(f"Error al obtener clientes: {str(e)}")
    
    def get_client(self, client_id=None, client_name=None):
        """Obtiene un cliente por ID o nombre"""
        self._ensure_table_exists()
        
        if not client_id and not client_name:
            raise ValidationError("Se debe proporcionar el ID o nombre del cliente")
        
        try:
            if client_id:
                query = text(f"SELECT * FROM {self.table_name} WHERE id = :client_id")
                result = db.session.execute(query, {'client_id': client_id})
            else:
                query = text(f"SELECT * FROM {self.table_name} WHERE name = :client_name")
                result = db.session.execute(query, {'client_name': client_name})
            
            row = result.fetchone()
            if not row:
                raise ResourceNotFoundError(f"Cliente no encontrado con {'ID' if client_id else 'nombre'}: {client_id or client_name}")
            
            client = {
                'id': row.id,
                'name': row.name,
                'api_key': row.api_key,
                'config': row.config,
                'active': row.active,
                'created_at': row.created_at,
                'updated_at': row.updated_at
            }
            return client
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener cliente: {str(e)}")
            raise ResourceNotFoundError(f"Error al obtener cliente: {str(e)}")
    
    def create_client(self, client_data):
        """Crea un nuevo cliente"""
        self._ensure_table_exists()
        
        # Validar datos requeridos
        if not client_data.get('name'):
            raise ValidationError("El nombre del cliente es obligatorio")
        if not client_data.get('api_key'):
            raise ValidationError("La API key del cliente es obligatoria")
        
        try:
            # Verificar si ya existe un cliente con ese nombre o API key
            query = text(f"""
            SELECT COUNT(*) as count FROM {self.table_name} 
            WHERE name = :name OR api_key = :api_key
            """)
            result = db.session.execute(query, {
                'name': client_data.get('name'),
                'api_key': client_data.get('api_key')
            })
            if result.fetchone().count > 0:
                raise ValidationError("Ya existe un cliente con ese nombre o API key")
            
            # Insertar nuevo cliente
            query = text(f"""
            INSERT INTO {self.table_name} (name, api_key, config, active)
            VALUES (:name, :api_key, :config, :active)
            RETURNING *
            """)
            result = db.session.execute(query, {
                'name': client_data.get('name'),
                'api_key': client_data.get('api_key'),
                'config': client_data.get('config', {}),
                'active': client_data.get('active', True)
            })
            db.session.commit()
            
            row = result.fetchone()
            new_client = {
                'id': row.id,
                'name': row.name,
                'api_key': row.api_key,
                'config': row.config,
                'active': row.active,
                'created_at': row.created_at,
                'updated_at': row.updated_at
            }
            logger.info(f"Cliente creado con éxito: {new_client['name']}")
            return new_client
        except ValidationError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error al crear cliente: {str(e)}")
            raise ValidationError(f"Error al crear cliente: {str(e)}")
    
    def update_client(self, client_id, client_data):
        """Actualiza un cliente existente"""
        self._ensure_table_exists()
        
        # Verificar que el cliente exista
        existing_client = self.get_client(client_id=client_id)
        
        try:
            # Preparar campos a actualizar
            update_fields = []
            params = {'client_id': client_id}
            
            if 'name' in client_data:
                update_fields.append("name = :name")
                params['name'] = client_data['name']
            
            if 'api_key' in client_data:
                update_fields.append("api_key = :api_key")
                params['api_key'] = client_data['api_key']
            
            if 'config' in client_data:
                update_fields.append("config = :config")
                params['config'] = client_data['config']
            
            if 'active' in client_data:
                update_fields.append("active = :active")
                params['active'] = client_data['active']
            
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            if not update_fields:
                return existing_client
            
            # Actualizar cliente
            query = text(f"""
            UPDATE {self.table_name}
            SET {', '.join(update_fields)}
            WHERE id = :client_id
            RETURNING *
            """)
            result = db.session.execute(query, params)
            db.session.commit()
            
            row = result.fetchone()
            updated_client = {
                'id': row.id,
                'name': row.name,
                'api_key': row.api_key,
                'config': row.config,
                'active': row.active,
                'created_at': row.created_at,
                'updated_at': row.updated_at
            }
            logger.info(f"Cliente actualizado con éxito: {updated_client['name']}")
            return updated_client
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error al actualizar cliente: {str(e)}")
            raise ValidationError(f"Error al actualizar cliente: {str(e)}")
    
    def delete_client(self, client_id):
        """Elimina un cliente existente"""
        self._ensure_table_exists()
        
        # Verificar que el cliente exista
        self.get_client(client_id=client_id)
        
        try:
            # Eliminar cliente
            query = text(f"DELETE FROM {self.table_name} WHERE id = :client_id")
            db.session.execute(query, {'client_id': client_id})
            db.session.commit()
            
            logger.info(f"Cliente eliminado con éxito. ID: {client_id}")
            return {"status": "success", "message": f"Cliente eliminado con éxito. ID: {client_id}"}
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            db.session.rollback()
            logger.error(f"Error al eliminar cliente: {str(e)}")
            raise ValidationError(f"Error al eliminar cliente: {str(e)}") 