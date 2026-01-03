import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ArrowLeft, ArrowRight, TrendingUp } from 'lucide-react';

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
  const { albumId } = useParams();
  const [matches, setMatches] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { t } = useTranslation();

  useEffect(() => {
    fetchMatches();
  }, [albumId]);

  const fetchMatches = async () => {
    try {
      const response = await api.get(`/matches?album_id=${albumId}`);
      setMatches(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
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
            data-testid="back-to-album-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate(`/albums/${albumId}`)}
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
              onClick={() => navigate(`/albums/${albumId}/inventory`)}
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
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 items-center">
                    <div>
                      <p className="text-sm font-semibold text-muted-foreground mb-2">{t('matches.youGive')}</p>
                      <div className="space-y-1">
                        {match.give_stickers.map((s) => (
                          <div key={s.id} className="text-sm bg-amber-100 dark:bg-amber-900/30 p-2 rounded">
                            #{s.number} {s.name}
                          </div>
                        ))}
                      </div>
                    </div>
                    <div className="flex justify-center">
                      <ArrowRight className="h-8 w-8 text-primary" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-muted-foreground mb-2">{t('matches.youGet')}</p>
                      <div className="space-y-1">
                        {match.get_stickers.map((s) => (
                          <div key={s.id} className="text-sm bg-emerald-100 dark:bg-emerald-900/30 p-2 rounded">
                            #{s.number} {s.name}
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  <div className="mt-4 p-3 bg-blue-50 rounded-lg text-sm">
                    <p className="font-semibold text-blue-900">
                      {t('matches.netGain')}: +{match.net_gain}
                    </p>
                  </div>
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
