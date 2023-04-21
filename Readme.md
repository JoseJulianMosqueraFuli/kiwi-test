# Kiwibot Test Backend

This is a sample API built using Python and Flask, with data stored in Firebase. It features endpoints to create, retrieve, and paginate deliveries and bots, as well as to assign bots to deliveries.

## Overview:

In this document you can find a detailed explanation of the project setup, technologies and available features.
This is the API built up to the deadline of the case study, in branch master.

## Index

1. [ Project sample ](#sample)
2. [ Getting started ](#getting-started)
3. [ Available endpoints ](#available-endpoints)

### Sample

The project looks and uses like shown in the video:

This is a very simple example, the way to use

### Getting started

To run this API on your local machine, follow these steps:

Clone the repository: git clone https://github.com/josejulianmosquera/kiwi-test.git
Navigate into the cloned directory: cd kiwi-test
Build and run the Docker container: docker-compose up --build
The API should now be available at http://localhost:5000.

### Available endpoints
## User
### POST 
Create user
```jsx
http://127.0.0.1:5000/signup_user
```
```jsx
{
    "email": "test2@example.com",
    "password": "contraseña2",
    "display_name": "test 2",
    "disabled": false
}
```
Login user
```jsx
http://127.0.0.1:5000/login_user
```
## Deliveries

### GET by ID or creator_ID
Get deliveries by ID (from delivery or creator_id
```jsx
http://localhost:5000/deliveries?creator_id=example&page=1&limit=10
http://localhost:5000/deliveries?id=example&page=1&limit=10
```

### POST

```jsx
http://127.0.0.1:5000/deliveries
```

**body**

```jsx
{
    "state": "pending",
    "pickup": {
        "pickup_lat": 11.11,
        "pickup_lon": -22.22
    },
    "dropoff": {
        "dropoff_lat": 33.33,
        "dropoff_lon": -44.444
    },
    "zone_id": "zone2"
}

```

## Bots

### GET by Zone_ID

```jsx
http://127.0.0.1:5000/bots?zone_id=zone1
```

### POST 

```jsx
http://127.0.0.1:5000/bots
```

**body**

```jsx
{
    "status": "available",
    "location": {
        "lat": 23.55,
        "lon": -67.99
    },
    "zone_id": "zone1"
}
```
### POST 

```jsx
http://127.0.0.1:5000/assign_bot
```

**body**

```jsx
{
    "bot_id": "836cc7bb-0d3f-4dfa-94f2-40a5181cae39",
    "delivery_id": "771916e4-55d1-46bc-b0b6-550d67ea3eeb"
}

```
### POST 

```jsx
http://127.0.0.1:5000/assign_bots_to_pending_deliveries
```

### Version

#### v1 deadline study case
##### Improvements:
  -keys security
  -test 
  -documentation.


### Author

Built by Jose Julian Mosquera Fuli.
