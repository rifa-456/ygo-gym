local s,id=GetID()
function s.initial_effect(c)
    local e=Effect.CreateEffect(c)
    e:SetType(EFFECT_TYPE_ACTIVATE)
    e:SetCode(EVENT_FREE_CHAIN)
    e:SetOperation(function() Duel.Win(PLAYER_NONE,0) end)
    c:RegisterEffect(e)
end
