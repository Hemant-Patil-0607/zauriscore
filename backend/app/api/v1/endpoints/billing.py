import stripe
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.models import User, BillingSubscription, PlanTier
from app.schemas.schemas import CheckoutSessionCreate, CheckoutSessionResponse, SubscriptionOut
from app.services.rate_limiter import rate_limiter

stripe.api_key = settings.stripe_secret_key

router = APIRouter(prefix="/billing", tags=["billing"])

PLAN_PRICE_MAP = {
    "pro": settings.stripe_pro_price_id,
    "enterprise": settings.stripe_enterprise_price_id,
}


@router.post("/checkout", response_model=CheckoutSessionResponse)
def create_checkout_session(
    body: CheckoutSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    price_id = PLAN_PRICE_MAP.get(body.plan)
    if not price_id:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {body.plan}")

    sub = db.query(BillingSubscription).filter(BillingSubscription.user_id == current_user.id).first()

    customer_id = sub.stripe_customer_id if sub else None

    if not customer_id:
        customer = stripe.Customer.create(email=current_user.email)
        customer_id = customer.id
        if sub:
            sub.stripe_customer_id = customer_id
            db.commit()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": 1}],
        mode="subscription",
        success_url=f"{settings.app_url}/billing/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.app_url}/billing",
        metadata={"user_id": str(current_user.id), "plan": body.plan},
    )

    return CheckoutSessionResponse(checkout_url=session.url)


@router.post("/webhook")
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing stripe-signature header")

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.stripe_webhook_secret
        )
    except (stripe.error.SignatureVerificationError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature or payload")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id = session.get("metadata", {}).get("user_id")
        plan_name = session.get("metadata", {}).get("plan", "pro")
        subscription_id = session.get("subscription")

        if user_id:
            plan_enum = PlanTier.pro if plan_name == "pro" else PlanTier.enterprise
            user = db.query(User).filter(User.id == user_id).first()
            if user:
                user.plan = plan_enum
                sub = db.query(BillingSubscription).filter(BillingSubscription.user_id == user.id).first()
                if sub:
                    sub.plan = plan_enum
                    sub.stripe_subscription_id = subscription_id
                    sub.status = "active"
                db.commit()

    elif event["type"] == "customer.subscription.deleted":
        subscription_id = event["data"]["object"]["id"]
        sub = db.query(BillingSubscription).filter(
            BillingSubscription.stripe_subscription_id == subscription_id
        ).first()
        if sub:
            sub.plan = PlanTier.free
            sub.status = "canceled"
            user = db.query(User).filter(User.id == sub.user_id).first()
            if user:
                user.plan = PlanTier.free
            db.commit()

    return {"status": "ok"}


@router.get("/subscription", response_model=SubscriptionOut)
def get_subscription(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sub = db.query(BillingSubscription).filter(BillingSubscription.user_id == current_user.id).first()
    if not sub:
        return SubscriptionOut(plan="free", status="active")
    return sub


@router.get("/usage")
def get_usage(current_user: User = Depends(get_current_user)):
    usage = rate_limiter.get_usage(str(current_user.id), current_user.plan.value)
    return usage
