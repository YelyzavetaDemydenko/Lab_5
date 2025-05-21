from fastapi import FastAPI, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.status import HTTP_302_FOUND
import csv

from Lab_1 import House, Tenant, Landlord, Contract

app = FastAPI()

templates = Jinja2Templates(directory="templates")

tenants_accounts = dict()
landlords_accounts = dict()
tenants = []
landlords = []
list_of_houses = []


def read_tenants(filename):
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 4:
                if row[3] != "None":
                    for house in list_of_houses:
                        if house.number == int(row[3]):
                            house_ = house
                            break
                else:
                    house_ = None
                tenants.append(Tenant(email = row[0], name = row[2], rental_house = house_))
                tenants_accounts[row[0]] = row[1]


def read_landlords(filename):
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 3:
                list_of_houses_ = []
                for house in list_of_houses:
                    if house.owner == row[0]:
                        list_of_houses_.append(house)
                landlords.append(Landlord(email = row[0], name = row[2], list_of_houses = list_of_houses_))
                landlords_accounts[row[0]] = row[1]


def read_houses(filename):
    with open(filename, newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if len(row) == 4:
                if row[2] == "True":
                    availability = True
                else:
                    availability = False
                list_of_houses.append(House(number = int(row[0]), price = row[1], availability = availability, owner = row[3]))


def update_landlords():
    with open("landlords.csv", 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for landlord in landlords:
            writer.writerow([landlord.email, landlords_accounts[landlord.email], landlord.name])


def update_tenants():
    with open("tenants.csv", 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for tenant in tenants:
            writer.writerow([tenant.email, tenants_accounts[tenant.email], tenant.name, tenant.rental_house.number if tenant.rental_house else "None"])


def update_houses():
    with open("list_of_houses.csv", 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for house in list_of_houses:
            writer.writerow([house.number, house.price, house.availability, house.owner])
        

read_houses("list_of_houses.csv")
read_landlords("landlords.csv")
read_tenants("tenants.csv")


@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/register_tenant")
def register_tenant_form(request: Request):
    return templates.TemplateResponse("register_tenant.html", {"request": request})


@app.post("/register_tenant")
def register_tenant(request: Request, email: str = Form(...), name: str = Form(...), password: str = Form(...)):
    if email == "" or name == "" or password == "":
        return templates.TemplateResponse("missing_info.html", {"request": request}, status_code=400)
    if email in tenants_accounts:
        return templates.TemplateResponse("register_error.html", {"request": request}, status_code=400)
    tenants_accounts[email] = password
    tenants.append(Tenant(email, name))

    with open("tenants.csv", 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([email, password, name, "None"])

    return RedirectResponse(url="/", status_code=HTTP_302_FOUND)


@app.get("/login_tenant")
def login_tenant_form(request: Request):
    return templates.TemplateResponse("login_tenant.html", {"request": request})


@app.post("/login_tenant")
def login_tenant(request: Request, email: str = Form(...), password: str = Form(...)):
    if email == "" or password == "":
        return templates.TemplateResponse("missing_info.html", {"request": request}, status_code=400)
    if tenants_accounts.get(email) == password:
        response = RedirectResponse(url="/tenant", status_code=HTTP_302_FOUND)
        response.set_cookie(key="tenant_email", value=email)
        return response
    return templates.TemplateResponse("login_error.html", {"request": request}, status_code=400)


@app.get("/tenant")
def tenant(request: Request):
    return templates.TemplateResponse("tenant.html", {"request": request})


@app.get("/tenant_info")
def tenant_info(request: Request):
    email = request.cookies.get("tenant_email")
    for tenant in tenants:
        if tenant.email == email:
            tenant_ = tenant
    if tenant_.rental_house is None:
        house_ = "Не орендує житло"
    else:
        house_ = "Орендує житло №" + str(tenant_.rental_house.number)
    return templates.TemplateResponse("tenant_info.html", {"request": request, "tenant": tenant_, "house_": house_})


@app.get("/tenant_edit_email")
def tenant_edit_email_form(request: Request):
    return templates.TemplateResponse("tenant_edit_email.html", {"request": request})


@app.post("/tenant_edit_email")
def tenant_edit_email(request: Request, new_email: str = Form(...)):
    old_email = request.cookies.get("tenant_email")

    if new_email == "":
        return templates.TemplateResponse("tenant_email_error_1.html", {"request": request}, status_code=400)
    if new_email in tenants_accounts:
        return templates.TemplateResponse("tenant_email_error_2.html", {"request": request}, status_code=400)
    
    for tenant in tenants:
        if tenant.email == old_email:
            tenant.email = new_email
            
            for email in tenants_accounts.keys():
                if email == old_email:
                    tenants_accounts[new_email] = tenants_accounts.pop(old_email)
                    break


    update_tenants()

    response = RedirectResponse(url="/tenant_info", status_code=302)
    response.set_cookie(key="tenant_email", value=new_email)
    return response


@app.get("/tenant_edit_name")
def tenant_edit_email_form(request: Request):
    return templates.TemplateResponse("tenant_edit_name.html", {"request": request})


@app.post("/tenant_edit_name")
def tenant_edit_email(request: Request, new_name: str = Form(...)):
    email = request.cookies.get("tenant_email")

    if new_name == "":
        return templates.TemplateResponse("tenant_name_error.html", {"request": request}, status_code=400)

    for tenant in tenants:
        if tenant.email == email:
            tenant.name = new_name

    update_tenants()
    
    return RedirectResponse(url="/tenant_info", status_code=302)


@app.get("/tenant_houses")
def tenant_houses(request: Request):
    return templates.TemplateResponse("tenant_houses.html", {"request": request, "houses": list_of_houses})


@app.get("/rent_house/{house_number}")
def rent_house_form(request: Request, house_number):
    email = request.cookies.get("tenant_email")
    for tenant in tenants:
        if tenant.email == email:
            tenant_ = tenant
    if tenant_.rental_house:
        return templates.TemplateResponse("rent_error.html", {"request": request})
    return templates.TemplateResponse("rent_house.html", {"request": request, "house_number": house_number})


@app.post("/rent_house/{house_number}")
def rent_house(request: Request, house_number: int, start_date: str = Form(...), end_date: str = Form(...)):
    email = request.cookies.get("tenant_email")
    for tenant in tenants:
        if tenant.email == email:
            tenant_ = tenant
    for house in list_of_houses:
        if house.number == house_number:
            for landlord in landlords:
                if landlord.email == house.owner:
                    landlord_ = landlord
            house_ = house

    contract = tenant_.rent_house(house_, landlord_, start_date, end_date)

    update_tenants()
    update_houses()

    return templates.TemplateResponse("contract_details.html", {"request": request, "contract": contract})


@app.get("/confirm_cancel_rent")
def confirm_cancel_rent(request: Request):
    email = request.cookies.get("tenant_email")
    for tenant in tenants:
        if tenant.email == email:
            tenant_ = tenant
    house = tenant_.rental_house
    return templates.TemplateResponse("confirm_cancel_rent.html", {"request": request, "house": house})


@app.get("/cancel_rent")
def cancel_rent(request: Request):
    email = request.cookies.get("tenant_email")
    for tenant in tenants:
        if tenant.email == email:
            tenant_ = tenant

    house_ = tenant_.rental_house
    tenant_.rental_house = None
    house_.availability = True

    update_houses()
    update_tenants()

    return RedirectResponse(url="/tenant_info", status_code=HTTP_302_FOUND)


@app.get("/register_landlord")
def register_landlord_form(request: Request):
    return templates.TemplateResponse("register_landlord.html", {"request": request})


@app.post("/register_landlord")
def register_landlord(request: Request, email: str = Form(...), name: str = Form(...), password: str = Form(...)):
    if email == "" or name == "" or password == "":
        return templates.TemplateResponse("missing_info.html", {"request": request}, status_code=400)
    if email in landlords_accounts:
        return templates.TemplateResponse("register_error.html", {"request": request}, status_code=400)
    landlords_accounts[email] = password
    landlords.append(Landlord(email, name))

    with open("landlords.csv", 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([email, password, name])

    return RedirectResponse(url="/", status_code=HTTP_302_FOUND)


@app.get("/login_landlord")
def login_landlord_form(request: Request):
    return templates.TemplateResponse("login_landlord.html", {"request": request})


@app.post("/login_landlord")
def login_landlord(request: Request, email: str = Form(...), password: str = Form(...)):
    if email == "" or password == "":
        return templates.TemplateResponse("missing_info.html", {"request": request}, status_code=400)
    if landlords_accounts.get(email) == password:
        response = RedirectResponse(url="/landlord", status_code=HTTP_302_FOUND)
        response.set_cookie(key="landlord_email", value=email)
        return response
    return templates.TemplateResponse("login_error.html", {"request": request}, status_code=400)


@app.get("/landlord")
def landlord(request: Request):
    return templates.TemplateResponse("landlord.html", {"request": request})


@app.get("/landlord_info")
def landlord_info(request: Request):
    email = request.cookies.get("landlord_email")
    for landlord in landlords:
        if landlord.email == email:
            landlord_ = landlord
    if landlord_.list_of_houses:
        houses = ", ".join("№"+str(house.number) for house in landlord_.list_of_houses)
    else:
        houses = "немає"
        
    return templates.TemplateResponse("landlord_info.html", {"request": request, "landlord": landlord_, "houses": houses})


@app.get("/landlord_edit_email")
def landlord_edit_email_form(request: Request):
    return templates.TemplateResponse("landlord_edit_email.html", {"request": request})


@app.post("/landlord_edit_email")
def landlord_edit_email(request: Request, new_email: str = Form(...)):
    old_email = request.cookies.get("landlord_email")

    if new_email == "":
        return templates.TemplateResponse("landlord_email_error_1.html", {"request": request}, status_code=400)
    if new_email in landlords_accounts:
        return templates.TemplateResponse("landlord_email_error_2.html", {"request": request}, status_code=400)

    for landlord in landlords:
        if landlord.email == old_email:
            landlord.email = new_email
            landlord_ = landlord
            
            
            for email in landlords_accounts.keys():
                if email == old_email:
                    landlords_accounts[new_email] = landlords_accounts.pop(old_email)
                    break
    
    for house in landlord_.list_of_houses:
        house.owner = landlord_.email

    update_landlords()
    if landlord_.list_of_houses:
        update_houses()

    response = RedirectResponse(url="/landlord_info", status_code=302)
    response.set_cookie(key="landlord_email", value=new_email)
    return response
        

@app.get("/landlord_edit_name")
def landlord_edit_email_form(request: Request):
    return templates.TemplateResponse("landlord_edit_name.html", {"request": request})


@app.post("/landlord_edit_name")
def landlord_edit_email(request: Request, new_name: str = Form(...)):
    email = request.cookies.get("landlord_email")

    if new_name == "":
        return templates.TemplateResponse("landlord_name_error.html", {"request": request}, status_code=400)

    for landlord in landlords:
        if landlord.email == email:
            landlord.name = new_name

    update_landlords()
    
    return RedirectResponse(url="/landlord_info", status_code=302)


@app.get("/landlord_houses")
def landlord_houses(request: Request):
    email = request.cookies.get("landlord_email")
    for landlord in landlords:
        if landlord.email == email:
            landlord_ = landlord
            break

    houses_with_tenants = []
    for house in landlord_.list_of_houses:
        tenant_ = None
        for tenant in tenants:
            if tenant.rental_house == house:
                tenant_ = tenant
                break  
        houses_with_tenants.append((house, tenant_))

    return templates.TemplateResponse("landlord_houses.html", {"request": request, "houses": houses_with_tenants})


@app.get("/add_house")
def add_house_form(request: Request):
    return templates.TemplateResponse("add_house.html", {"request": request})


@app.post("/add_house")
def add_house_email(request: Request, price: float = Form(...)):
    email = request.cookies.get("landlord_email")
    for landlord in landlords:
        if landlord.email == email:
            landlord_ = landlord
    house = House(price)
    landlord_.add_house(house)
    list_of_houses.append(house)

    with open("list_of_houses.csv", 'a', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow([house.number, house.price, house.availability, house.owner])

    return RedirectResponse(url="/landlord_houses", status_code=302)


@app.get("/confirm_delete_house/{house_number}")
def confirm_delete_house(request: Request, house_number):
    return templates.TemplateResponse("confirm_delete_house.html", {"request": request, "house_number": house_number})


@app.get("/delete_house/{house_number}")
def delete_house(request: Request, house_number):
    email = request.cookies.get("landlord_email")
    for landlord in landlords:
        if landlord.email == email:
            landlord_ = landlord
            break

    for house in list_of_houses:
        if house.number == int(house_number):
            house_ = house
            break

    landlord_.list_of_houses.remove(house_)
    list_of_houses.remove(house_)
            
    update_houses()
    
    for tenant in tenants:
        if tenant.rental_house == house_:
            tenant.rental_house = None
            update_tenants()
            break 

    return RedirectResponse(url="/landlord_houses", status_code=302)

