import React, { useState, useEffect, useContext } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api, AuthContext } from '../App';
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Plus, Users, Settings as SettingsIcon } from 'lucide-react';

export const Groups = () => {
  const [groups, setGroups] = useState([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [groupName, setGroupName] = useState('');
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { user } = useContext(AuthContext);

  useEffect(() => {
    fetchGroups();
  }, []);

  const fetchGroups = async () => {
    try {
      const response = await api.get('/groups');
      setGroups(response.data);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateGroup = async (e) => {
    e.preventDefault();
    try {
      const response = await api.post('/groups', { name: groupName });
      toast.success(t('common.success'));
      setCreateDialogOpen(false);
      setGroupName('');
      navigate(`/groups/${response.data.id}`);
    } catch (error) {
      toast.error(error.response?.data?.detail || t('common.error'));
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
    <div className="min-h-screen bg-background">
      <div className="max-w-7xl mx-auto p-6">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-4xl font-black tracking-tight text-primary">{t('groups.title')}</h1>
            <p className="text-muted-foreground mt-2">{user?.email}</p>
          </div>
          <Button
            data-testid="settings-btn"
            variant="outline"
            size="icon"
            onClick={() => navigate('/settings')}
          >
            <SettingsIcon className="h-5 w-5" />
          </Button>
        </div>

        {groups.length === 0 ? (
          <div className="text-center py-20" data-testid="no-groups-message">
            <Users className="h-24 w-24 mx-auto text-muted-foreground mb-4" />
            <h2 className="text-2xl font-bold mb-2">{t('groups.noGroups')}</h2>
            <p className="text-muted-foreground mb-6">{t('groups.createFirst')}</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="groups-grid">
            {groups.map((group) => (
              <Card
                key={group.id}
                data-testid={`group-card-${group.id}`}
                className="hover:shadow-lg transition-all duration-300 cursor-pointer border-2 hover:border-primary"
                onClick={() => navigate(`/groups/${group.id}`)}
              >
                <CardHeader>
                  <CardTitle className="text-xl font-bold">{group.name}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    {new Date(group.created_at).toLocaleDateString()}
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}

        <Dialog open={createDialogOpen} onOpenChange={setCreateDialogOpen}>
          <DialogTrigger asChild>
            <Button
              data-testid="create-group-btn"
              className="fixed bottom-8 right-8 h-14 w-14 rounded-full shadow-2xl btn-primary"
              size="icon"
            >
              <Plus className="h-6 w-6" />
            </Button>
          </DialogTrigger>
          <DialogContent data-testid="create-group-dialog">
            <DialogHeader>
              <DialogTitle>{t('groups.createGroup')}</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleCreateGroup} className="space-y-4">
              <Input
                data-testid="group-name-input"
                placeholder={t('groups.groupName')}
                value={groupName}
                onChange={(e) => setGroupName(e.target.value)}
                required
              />
              <div className="flex gap-2">
                <Button
                  data-testid="create-group-submit-btn"
                  type="submit"
                  className="flex-1 btn-primary"
                >
                  {t('groups.create')}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setCreateDialogOpen(false)}
                >
                  {t('groups.cancel')}
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </div>
  );
};

export default Groups;
