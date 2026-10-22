local s,id=GetID()
function s.initial_effect(c)
    local e=Effect.CreateEffect(c)
    e:SetType(EFFECT_TYPE_ACTIVATE)
    e:SetCode(EVENT_FREE_CHAIN)
    local table_key={}
    local function_key=function() return 1 end
    local keys={[c]=1,[e]=2,[table_key]=3,[function_key]=4,[math.abs]=5}
    e:SetOperation(function(effect,tp)
        Duel.SelectYesNo(tp,0)
        assert(keys[c]==1 and keys[effect]==2)
        assert(keys[table_key]==3 and keys[function_key]==4 and keys[math.abs]==5)
        Duel.Damage(1-tp,400,REASON_EFFECT)
    end)
    c:RegisterEffect(e)
end
