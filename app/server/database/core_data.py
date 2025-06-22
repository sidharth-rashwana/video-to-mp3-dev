from typing import Any, Union
from app.server.database.db import mongo
from app.server.utils import date_utils
from fastapi.encoders import jsonable_encoder
from pymongo.collection import ReturnDocument
from pydantic import EmailStr
from bson.objectid import ObjectId
from app.server.utils import date_utils


async def create_one(collection_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Insert one operation on database

    Returns:
        dict[str, Any]: inserted document
    """
    try:
        collection = mongo.get_collection(collection_name)
        if "_id" not in data:
            data["_id"] =  str(ObjectId())  # Generate a unique string ID if _id is not provided
        
        timestamp = date_utils.get_current_timestamp()
        data.update({'createdAt':timestamp})
        result = await collection.insert_one(data)
    except Exception as e:
        raise Exception("Failed to insert document: " + str(e))

    if not result.acknowledged:
        raise Exception("Failed to acknowledge document insertion")

    return {'acknowledge': result.acknowledged, '_id': data["_id"], 'status': 'SUCCESS'}

async def create_many(collection_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Insert one operation on database

    Returns:
        dict[str, Any]: inserted document acknowledgement and id
    """
    try:
        collection = mongo.get_collection(collection_name)
        result = await collection.insert_many(data)
    except Exception as e:
        raise Exception("Failed to insert document: " + str(e))

    if not result.acknowledged:
        raise Exception("Failed to acknowledge document insertion")
    
    return {'acknowledge':result.acknowledged,'_id':str(result.inserted_ids),'status': 'SUCCESS'}
    

async def read_one(collection_name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Read one operation on database

    Returns:
        dict[str, Any]: response
    """
    try:
        collection = mongo.get_collection(collection_name)
        result = await collection.find_one(data)

        if result is None:
            return {'status':404,'msg':'not found'}
        
        result = dict(result)
        result['status']=200
        return result
    
    except Exception as e:
        raise Exception(str(e))
    
async def read_many(collection_name: str,filter: dict[str, Any],exclude=None) -> list[dict[str, Any]]:
    """Read all documents based on filter

    Returns:
        list[dict[str, Any]]: response
    """
    try:
        projection = None
        if exclude:
            projection = {field: 0 for field in exclude}  # Create projection to exclude fields
        collection = mongo.get_collection(collection_name)
        cursor = collection.find(filter, projection=projection)
        documents = await cursor.to_list(length=None)
        return documents
    
    except Exception as e:
            raise Exception(str(e))

async def read_all(collection_name: str) -> list[dict[str, Any]]:
    """Read all documents

    Returns:
        list[dict[str, Any]]: response
    """
    try:
        collection = mongo.get_collection(collection_name)
        cursor = collection.find()
        documents = await cursor.to_list(length=None)
        return documents
    
    except Exception as e:
            raise Exception(str(e))
    

async def update_one(collection_name: str, filter_by, update_by) -> dict[str, Any]:
    """update one operation on database

    Returns:
        dict[str, Any]: response
    """
    try:
        collection = mongo.get_collection(collection_name)
        result = await collection.find_one_and_update(filter_by, update_by, return_document =ReturnDocument.AFTER)
        if not result:
            raise Exception("Update failed: Document not found")
        return result
    except Exception as e:
        raise Exception(f"Update failed: {e}")


async def update_many(collection_name: str, filter_by: dict, update_data: dict) -> dict[str, Any]:
    """Update multiple documents in collection in database

    Args:
        collection_name (str): Name of the collection to update
        filter_by (dict): Filter criteria to select documents for update
        update_data (dict): Data to update in the selected documents

    Returns:
        dict[str, Any]: Response
    """
    try:
        collection = mongo.get_collection(collection_name)
        
        result = await collection.update_many(filter_by, {"$set": update_data})
        if result.matched_count == 0:
            return {'status': 'No matching records found'}
        
        if not result.acknowledged:
            raise Exception("Failed to acknowledge Record update")

        return {'acknowledge': result.acknowledged, 'matched_count': result.matched_count, 'status': 'SUCCESS'}
    
    except Exception as e:
        raise Exception(f"Update failed: {e}")


async def delete_one(collection_name: str, filter_by) -> dict[str, Any]:
    """delete one document from collection in database


    Returns:
        dict[str, Any]: response
    """
    try:
        collection = mongo.get_collection(collection_name)
        result = await collection.delete_one(filter_by)
        if result.deleted_count == 0:
            return {'status':404,'msg':'not found'}
        
        if not result.acknowledged:
            raise Exception("Failed to acknowledge Record deletion")

        return {'acknowledge':result.acknowledged,'msg':f'Record is Successfully Deleted.'}
    
    except Exception as e:
        raise Exception(f"Delete failed: {e}")

async def delete_many(collection_name: str, id_list: list[str]) -> dict[str, Any]:
    """Delete multiple documents from collection in database based on _id list

    Args:
        collection_name (str): Name of the collection to delete from
        id_list (list[str]): List of _id values to filter documents for deletion

    Returns:
        dict[str, Any]: Response
    """
    try:
        collection = mongo.get_collection(collection_name)
        
        filter_by = {"_id": {"$in": id_list}}
        
        result = await collection.delete_many(filter_by)
        if result.deleted_count == 0:
            return {'status': 404, 'msg': 'No matching records found'}
        
        if not result.acknowledged:
            raise Exception("Failed to acknowledge Record deletion")

        return {'acknowledge': result.acknowledged, 'msg': f'{result.deleted_count} records successfully deleted.'}
    
    except Exception as e:
        raise Exception(f"Delete failed: {e}")

async def delete_all(collection_name: str) -> dict[str, Any]:
    """delete all documents from collection in database


    Returns:
        dict[str, Any]: response
    """
    try:
        collection = mongo.get_collection(collection_name)
        result = await collection.delete_many({})
        
        if result is None:
            return {'status':404,'msg':'No element present to delete'}
        
        if not result.acknowledged:
            raise Exception("Failed to acknowledge documents deletion")
        

        return {'acknowledge':result.acknowledged,'deletedCount':f'Total records deleted {result.deleted_count}'}
    
    except Exception as e:
        raise Exception(f"Delete failed: {e}")

async def query_read(collection_name: str, aggregate: list) -> dict:
    collection = mongo.get_collection(collection_name)
    model_list = []

    data = collection.aggregate(aggregate)
    async for model in data:
        model_list.append(model)
    return model_list
