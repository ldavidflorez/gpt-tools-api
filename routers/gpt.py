from fastapi import Depends, APIRouter
from fastapi.responses import JSONResponse
from typing import List
from sqlalchemy.orm import Session
import models.models as models
from database.database import get_db
from pydantic import BaseModel
from routers.auth import get_current_user, get_user_exception, get_permissions_exception
from utils.openai_api import get_response

from transformers import GPT2TokenizerFast

import os

MAX_TOKENS = int(os.environ["MAX_TOKENS"])

tokenizer = GPT2TokenizerFast.from_pretrained("gpt2")

router = APIRouter(prefix="/api/v1/services/gpt-3",
                   tags=["GPT-3"])


def capacity_token_count(db, user_id, service_id, prompt_template):
    tokens_to_consume = len(tokenizer(prompt_template)["input_ids"])
    available_tokens = db.query(models.Permissions).filter(models.Permissions.service_id == service_id).filter(
        models.Permissions.user_id == user_id).first().available_tokens
    if tokens_to_consume > available_tokens:
        return JSONResponse(
            status_code=402, content={"detail": "You do not have enough tokens available.", "tokens_to_consume": tokens_to_consume, "available_tokens": available_tokens})
    return None


def maximum_token_count(prompt_template):
    max_tokens = MAX_TOKENS
    tokens_to_consume = len(tokenizer(prompt_template)["input_ids"])
    if tokens_to_consume > max_tokens:
        return JSONResponse(status_code=413, content={
            "detail": "Maximum capacity of tokens per request exceeded.", "maximum_allowed": max_tokens})
    return None


def check_if_service_is_activate(db, service_id):
    is_active = db.query(models.Services).filter(
        models.Services.id == service_id).first().is_active
    if not is_active:
        return JSONResponse(status_code=409, content={
            "detail": "The service was deactivated."})
    return None


class PromptBase(BaseModel):
    sentence: str


class PromptTranslation(BaseModel):
    sentence: str
    source: str
    target: str


class PromptIntent(BaseModel):
    sentence: str
    tags: List[str]


class PromptWriter(BaseModel):
    message_type: str
    sender: str
    recipient: str
    tags: List[str]
    word_limit: int


@router.post("/lang-detection")
async def lang_detection(prompt: PromptBase, user: dict = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    service_id = 1

    if user is None:
        raise get_user_exception()

    response = check_if_service_is_activate(db, service_id)
    if response is not None:
        return response

    if service_id not in user["permissions"]:
        raise get_permissions_exception()

    prompt_template = f"Tell me what language this is sentence '{prompt.sentence}'. For example: english, spanish, french, etc."

    response = maximum_token_count(prompt_template)
    if response is not None:
        return response

    if user["subscription"] != "premium":
        response = capacity_token_count(
            db, user["id"], service_id, prompt_template)
        if response is not None:
            return response

    response = get_response(prompt_template)

    consumed_tokens = response.usage.total_tokens

    tracker_model = models.Tracking()
    tracker_model.user_id = user["id"]
    tracker_model.service_id = service_id
    tracker_model.consumed_tokens = consumed_tokens

    if user["subscription"] != "premium":
        service_state = db.query(models.Permissions).filter(models.Permissions.user_id == user["id"]).filter(
            models.Permissions.service_id == service_id).first()
        service_state.available_tokens -= consumed_tokens
        db.add(service_state)
        db.commit()

    db.add(tracker_model)
    db.commit()

    return response


@router.post("/lang-translation")
async def lang_translation(prompt: PromptTranslation, user: dict = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    service_id = 2

    if user is None:
        raise get_user_exception()

    response = check_if_service_is_activate(db, service_id)
    if response is not None:
        return response

    if service_id not in user["permissions"]:
        raise get_permissions_exception()

    prompt_template = f"Translate this sentence from {prompt.source} to {prompt.target}: '{prompt.sentence}'"

    response = maximum_token_count(prompt_template)
    if response is not None:
        return response

    if user["subscription"] != "premium":
        response = capacity_token_count(
            db, user["id"], service_id, prompt_template)
        if response is not None:
            return response

    response = get_response(prompt_template)

    consumed_tokens = response.usage.total_tokens

    tracker_model = models.Tracking()
    tracker_model.user_id = user["id"]
    tracker_model.service_id = service_id
    tracker_model.consumed_tokens = response.usage.total_tokens

    if user["subscription"] != "premium":
        service_state = db.query(models.Permissions).filter(models.Permissions.user_id == user["id"]).filter(
            models.Permissions.service_id == service_id).first()
        service_state.available_tokens -= consumed_tokens
        db.add(service_state)
        db.commit()

    db.add(tracker_model)
    db.commit()

    return response


@router.post("/sentiment-detect")
async def sentiment_detect(prompt: PromptBase, user: dict = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    service_id = 3

    if user is None:
        raise get_user_exception()

    response = check_if_service_is_activate(db, service_id)
    if response is not None:
        return response

    if service_id not in user["permissions"]:
        raise get_permissions_exception()

    prompt_template = f"Classify the following sentence as negative, neutral or positive: '{prompt.sentence}'"

    response = maximum_token_count(prompt_template)
    if response is not None:
        return response

    if user["subscription"] != "premium":
        response = capacity_token_count(
            db, user["id"], service_id, prompt_template)
        if response is not None:
            return response

    response = get_response(prompt_template)

    consumed_tokens = response.usage.total_tokens

    tracker_model = models.Tracking()
    tracker_model.user_id = user["id"]
    tracker_model.service_id = service_id
    tracker_model.consumed_tokens = response.usage.total_tokens

    if user["subscription"] != "premium":
        service_state = db.query(models.Permissions).filter(models.Permissions.user_id == user["id"]).filter(
            models.Permissions.service_id == service_id).first()
        service_state.available_tokens -= consumed_tokens
        db.add(service_state)
        db.commit()

    db.add(tracker_model)
    db.commit()

    return response


@router.post("/intent-detection")
async def intent_detection(prompt: PromptIntent, user: dict = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    service_id = 4

    if user is None:
        raise get_user_exception()

    response = check_if_service_is_activate(db, service_id)
    if response is not None:
        return response

    if service_id not in user["permissions"]:
        raise get_permissions_exception()

    tags = " or ".join(prompt.tags)
    prompt_template = f"Is the intent behind the following text {tags}: '{prompt.sentence}'.Please, only give me a option into tags."

    response = maximum_token_count(prompt_template)
    if response is not None:
        return response

    if user["subscription"] != "premium":
        response = capacity_token_count(
            db, user["id"], service_id, prompt_template)
        if response is not None:
            return response

    response = get_response(prompt_template)

    consumed_tokens = response.usage.total_tokens

    tracker_model = models.Tracking()
    tracker_model.user_id = user["id"]
    tracker_model.service_id = service_id
    tracker_model.consumed_tokens = response.usage.total_tokens

    if user["subscription"] != "premium":
        service_state = db.query(models.Permissions).filter(models.Permissions.user_id == user["id"]).filter(
            models.Permissions.service_id == service_id).first()
        service_state.available_tokens -= consumed_tokens
        db.add(service_state)
        db.commit()

    db.add(tracker_model)
    db.commit()

    return response


@router.post("/summarize")
async def summarize(prompt: PromptBase, user: dict = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    service_id = 5

    if user is None:
        raise get_user_exception()

    response = check_if_service_is_activate(db, service_id)
    if response is not None:
        return response

    response = check_if_service_is_activate(db, service_id)
    if response is not None:
        return response

    if service_id not in user["permissions"]:
        raise get_permissions_exception()

    prompt_template = f"Extract the key points from this message: '{prompt.sentence}'"

    response = maximum_token_count(prompt_template)
    if response is not None:
        return response

    if user["subscription"] != "premium":
        response = capacity_token_count(
            db, user["id"], service_id, prompt_template)
        if response is not None:
            return response

    response = get_response(prompt_template)

    consumed_tokens = response.usage.total_tokens

    tracker_model = models.Tracking()
    tracker_model.user_id = user["id"]
    tracker_model.service_id = service_id
    tracker_model.consumed_tokens = response.usage.total_tokens

    if user["subscription"] != "premium":
        service_state = db.query(models.Permissions).filter(models.Permissions.user_id == user["id"]).filter(
            models.Permissions.service_id == service_id).first()
        service_state.available_tokens -= consumed_tokens
        db.add(service_state)
        db.commit()

    db.add(tracker_model)
    db.commit()

    return response


@router.post("/writer")
async def writer(prompt: PromptWriter, user: dict = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    service_id = 6

    if user is None:
        raise get_user_exception()

    response = check_if_service_is_activate(db, service_id)
    if response is not None:
        return response

    if service_id not in user["permissions"]:
        raise get_permissions_exception()

    tags = ", ".join(prompt.tags)
    prompt_template = f'''
    Create a {prompt.message_type} with next considerations:

    1. Customer Name: {prompt.recipient}
    2. Bullet points: {tags}.
    3. Write the message in {prompt.word_limit} words
    
    And finally, regards from sender: {prompt.sender}
    '''

    response = maximum_token_count(prompt_template)
    if response is not None:
        return response

    if user["subscription"] != "premium":
        response = capacity_token_count(
            db, user["id"], service_id, prompt_template)
        if response is not None:
            return response

    response = get_response(prompt_template)

    consumed_tokens = response.usage.total_tokens

    tracker_model = models.Tracking()
    tracker_model.user_id = user["id"]
    tracker_model.service_id = service_id
    tracker_model.consumed_tokens = response.usage.total_tokens

    if user["subscription"] != "premium":
        service_state = db.query(models.Permissions).filter(models.Permissions.user_id == user["id"]).filter(
            models.Permissions.service_id == service_id).first()
        service_state.available_tokens -= consumed_tokens
        db.add(service_state)
        db.commit()

    db.add(tracker_model)
    db.commit()

    return response
