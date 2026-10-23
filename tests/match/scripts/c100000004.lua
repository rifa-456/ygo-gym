local s,id=GetID()
function s.initial_effect(c)
    local e=Effect.CreateEffect(c)
    e:SetType(EFFECT_TYPE_SINGLE)
    e:SetCode(EFFECT_MATCH_KILL)
    c:RegisterEffect(e)
end
