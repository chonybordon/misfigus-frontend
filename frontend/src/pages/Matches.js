import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, TrendingUp } from 'lucide-react';

const maskEmail = (email) => {
  if (!email) return '';
  const [local, domain] = email.split('@');
  if (local.length <= 3) {
    return `${local[0]}***@${domain}`;
  }
  return `${local.substring(0, 3)}***@${domain}`;
};

const getDisplayName = (user, t) => {
  if (!user) return t('app.defaultUser');
  
  // Priority 1: Display name if exists
  if (user.display_name && user.display_name.trim()) {
    return user.display_name.trim();
  }
  
  // Priority 2: Check for test/demo accounts
  if (user.email) {
    const prefix = user.email.split('@')[0].trim().toLowerCase();
    
    const testMappings = {
      'user': t('members.testUser'),
      'newuser': t('members.newTestUser'),
      'testuser': t('members.testUser'),
      'test': t('members.testUser'),
      'demo': t('members.testUser'),
      'testactivation': t('members.technicalAccount')
    };
    
    if (testMappings[prefix]) {
      return testMappings[prefix];
    }
    
    // Priority 3: Masked email
    return maskEmail(user.email);
  }
  
  return t('app.defaultUser');
};

export const Matches = () => {
  const { groupId, albumId } = useParams();
  const contextId = groupId || albumId; // Support both group and album routes
  const isGroupContext = !!groupId;
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchMatches();
  }, [contextId]);

  const fetchMatches = async () => {
    try {
      // Use group endpoint if groupId, otherwise album endpoint
      const endpoint = isGroupContext 
        ? `/groups/${contextId}/matches`
        : `/matches?album_id=${contextId}`;
      const response = await api.get(endpoint);
      setMatches(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  // Get back navigation path
  const getBackPath = () => {
    return isGroupContext ? `/groups/${contextId}` : `/albums/${contextId}`;
  };

  // Get inventory path
  const getInventoryPath = () => {
    return isGroupContext ? `/groups/${contextId}/inventory` : `/albums/${contextId}/inventory`;
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-2xl font-bold">{t('common.loading')}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen sticker-album-pattern pb-20">
      <div className="max-w-4xl mx-auto p-6">
        <div className="flex items-center gap-4 mb-8">
          <Button
            data-testid="back-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate(getBackPath())}
          >
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-3xl font-black tracking-tight text-primary">{t('matches.title')}</h1>
        </div>

        {matches.length === 0 ? (
          <div className="text-center py-20" data-testid="no-matches-message">
            <TrendingUp className="h-24 w-24 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-2xl font-bold mb-2">{t('matches.noMatches')}</h2>
            <p className="text-muted-foreground mb-6">{t('matches.updateInventory')}</p>
            <Button
              className="btn-primary"
              onClick={() => navigate(getInventoryPath())}
            >
              {t('inventory.title')}
            </Button>
          </div>
        ) : (
          <div className="space-y-4" data-testid="matches-list">
            {matches.map((match, index) => (
              <Card key={index} data-testid={`match-card-${index}`} className="hover:shadow-lg transition-all">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <div className="h-10 w-10 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold">
                      {getDisplayName(match.user, t)[0].toUpperCase()}
                    </div>
                    <span>{getDisplayName(match.user, t)}</span>
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-wrap gap-2 mb-4">
                    {match.has_stickers_i_need && (
                      <span className="text-sm bg-emerald-100 dark:bg-emerald-900/30 text-emerald-800 dark:text-emerald-200 px-3 py-1 rounded-full">
                        {t('matches.hasStickersINeed')}
                      </span>
                    )}
                    {match.needs_stickers_i_have && (
                      <span className="text-sm bg-amber-100 dark:bg-amber-900/30 text-amber-800 dark:text-amber-200 px-3 py-1 rounded-full">
                        {t('matches.needsStickersIHave')}
                      </span>
                    )}
                    {match.can_exchange && (
                      <span className="text-sm bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200 px-3 py-1 rounded-full font-semibold">
                        {t('matches.canExchange')}
                      </span>
                    )}
                  </div>
                  {match.can_exchange && (
                    <Button
                      className="w-full"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleCreateExchange(match.user.id);
                      }}
                    >
                      {t('exchange.coordinateExchange')}
                    </Button>
                  )}
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default Matches;
