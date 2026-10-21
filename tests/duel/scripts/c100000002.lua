local s,id=GetID()
function s.initial_effect(c)
    local e=Effect.CreateEffect(c)
    e:SetType(EFFECT_TYPE_ACTIVATE)
    e:SetCode(EVENT_FREE_CHAIN)
    e:SetOperation(s.operation)
    c:RegisterEffect(e)
end
function s.operation(e,tp)
    local random=math.random
    local sampled=random(1,1000000)
    Duel.SelectYesNo(tp,1)
    Duel.SetLP(tp,random(1,1000000))
    Duel.SetLP(1-tp,Duel.GetRandomNumber(1,1000000))
    Duel.SelectYesNo(tp,sampled)
end
