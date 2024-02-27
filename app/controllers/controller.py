from collections import Counter
from app.database.schema import ClientSchema, PictureSchema, ReportInterface, UploadFileInterface
from app.service.service import Service
from fastapi import APIRouter, HTTPException, UploadFile
from fastapi_utils.cbv import cbv
from uuid import uuid4
from app.database.repository import Repository

router = APIRouter()

@cbv(router)
class Controller:
    def __init__(self):
        self.repository = Repository()
        self.service = Service()

    @router.post("/create_login", status_code=201)
    def create_login(self, email: str, password: str):
        client_uuid = f'client_{str(uuid4())}'
        client_schema = ClientSchema(
            client_uuid=client_uuid,
            email=email,
            password=password
        )
        self.repository.insert_client(**client_schema.dict())
        return {
            "client_uuid": client_uuid,
            "email": email,
        }

    @router.post("/login", status_code=201)
    def do_login(self, email: str, password: str):
        try:
            login_info = self.repository.get_login(email=email)
            if login_info:
                if login_info.password == password:
                    return {
                        "email": login_info.email,
                        "client_uuid": login_info.client_uuid
                    }
                else:
                    raise HTTPException(status_code=400, detail="Senha incorreta")
        except Exception:
            raise HTTPException(status_code=400, detail="Usuário não encontrado")
        
    @router.post("/upload")
    def upload_file(self, picture: UploadFileInterface):
        picture_extrated_info = self.service.extract_info_from_image(
            picture.base64_encoded_data)

        # Parse extracted info with defaults
        is_heathy = picture_extrated_info.get('saudável', True)
        ingredients = picture_extrated_info.get(
            'ingredientes',
            ['arroz', 'feijão', 'carne', 'alface', 'tomate']
        )
        total_calories = picture_extrated_info.get('calorias', 650)
        nutrients = picture_extrated_info.get(
            'nutrientes',
            ['proteína', 'fibra dietética', 'vitamina C', 'ferro', 'cálcio']
        )

        picture_schema = PictureSchema(
            picture_uuid=f'picture_{str(uuid4())}',
            client_uuid=picture.client_uuid,
            name=picture.name,
            file_name=picture.name,
            is_healty=is_heathy,
            ingredients=ingredients,
            total_calories=total_calories,
            nutrients=nutrients,
            picture_base_64=picture.base64_encoded_data
        )
        self.repository.insert_picture(**picture_schema.dict())
    
    @router.get("/get_weekly_report")
    def get_weekly_report(self):
        meals = self.repository.get_all_pictures()
        healthy_counter = Counter([meal.is_healty for meal in meals])
        total_calories = sum([int(meal.total_calories) for meal in meals])
        average_calories = total_calories / len(meals)
        return ReportInterface(
            healthy_meals=healthy_counter[True],
            total_meals=len(meals),
            unhealthy_meals=healthy_counter[False],
            total_calories=total_calories,
            average_calories=average_calories
        )

    @router.get("/get_info/{client_uuid}")
    def get_picture_info(self, client_uuid: str, picture_uuid: str):
        pass

    @router.get("/get_meals_list")
    def get_meals_list(self, client_uuid: str):
        return self.repository.get_all_pictures(client_uuid=client_uuid)
