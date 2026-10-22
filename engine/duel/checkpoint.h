#pragma once
#include <memory>
namespace ygo_gym {
class Duel;
class Checkpoint {
  public:
    ~Checkpoint();
    Checkpoint(const Checkpoint &) = delete;
    Checkpoint &operator=(const Checkpoint &) = delete;

  private:
    friend class Duel;
    struct Data;
    explicit Checkpoint(std::unique_ptr<Data> data);
    std::unique_ptr<Data> data_;
};
} // namespace ygo_gym
